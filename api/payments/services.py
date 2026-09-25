import hmac
import hashlib

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils import timezone

from hire_requests.models import HireRequest, HireRequestStatus
from payments.models import Payment, PaymentStatus, Payout, PayoutStatus
from payments.razorpay import RazorpayError, create_razorpay_order


class PaymentServiceError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


def _active_payment(hire_request: HireRequest) -> Payment | None:
    return (
        Payment.objects.filter(hire_request=hire_request)
        .exclude(status=PaymentStatus.FAILED)
        .order_by("-created_at")
        .first()
    )


@transaction.atomic
def create_payment_order(user, hire_request_id) -> tuple[Payment, bool]:
    if not hasattr(user, "profile"):
        raise PaymentServiceError("forbidden", "Profile required.")
    try:
        hire_request = (
            HireRequest.objects.select_for_update()
            .select_related("listing", "hirer", "coach")
            .get(pk=hire_request_id)
        )
    except HireRequest.DoesNotExist:
        raise PaymentServiceError("not_found", "Hire request not found.")

    if user.profile.pk != hire_request.hirer_id:
        raise PaymentServiceError("forbidden", "Only the hirer can pay this request.")
    if hire_request.status != HireRequestStatus.ACCEPTED:
        raise PaymentServiceError("invalid_state", "Only an accepted request can be paid.")

    existing = _active_payment(hire_request)
    if existing:
        if existing.status in (PaymentStatus.CAPTURED, PaymentStatus.REFUNDED):
            raise PaymentServiceError("already_paid", "This request is already paid.")
        return existing, False

    amount_paise = hire_request.listing.rate_rupees * 100
    try:
        order = create_razorpay_order(
            amount_paise=amount_paise,
            receipt=str(hire_request.id),
            notes={"hire_request_id": str(hire_request.id)},
        )
    except RazorpayError as exc:
        code = "not_configured" if "not configured" in exc.detail.lower() else "gateway_error"
        raise PaymentServiceError(code, exc.detail) from exc

    try:
        payment = Payment.objects.create(
            hire_request=hire_request,
            hirer=hire_request.hirer,
            coach=hire_request.coach,
            amount_paise=amount_paise,
            currency="INR",
            status=PaymentStatus.CREATED,
            razorpay_order_id=order["id"],
            rate_rupees=hire_request.listing.rate_rupees,
            rate_unit=hire_request.listing.rate_unit,
        )
    except IntegrityError:
        existing = _active_payment(hire_request)
        if existing:
            return existing, False
        raise
    return payment, True


def signatures_match(expected: str, provided: str) -> bool:
    if not provided or not isinstance(provided, str):
        return False
    try:
        return hmac.compare_digest(expected, provided)
    except (TypeError, ValueError):
        return False


def checkout_signature_ok(order_id: str, payment_id: str, signature: str) -> bool:
    secret = settings.RAZORPAY_KEY_SECRET or ""
    digest = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return signatures_match(digest, signature)


def webhook_signature_ok(body: bytes, signature: str) -> bool:
    secret = settings.RAZORPAY_WEBHOOK_SECRET or ""
    if not secret:
        return False
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return signatures_match(digest, signature)


def _send_receipt(payment: Payment):
    rupees = payment.amount_paise / 100
    send_mail(
        subject="ForHire payment received",
        message=(
            f"We received ₹{rupees:.2f} for your hire request {payment.hire_request_id}. "
            "The coach is paid out separately by ForHire."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[payment.hirer.email],
        fail_silently=True,
    )


@transaction.atomic
def capture_payment(*, order_id: str, razorpay_payment_id: str, amount_paise: int | None = None) -> Payment:
    try:
        payment = Payment.objects.select_for_update().get(razorpay_order_id=order_id)
    except Payment.DoesNotExist:
        raise PaymentServiceError("not_found", "Unknown order.")

    if (
        payment.status == PaymentStatus.CAPTURED
        and payment.razorpay_payment_id == razorpay_payment_id
    ):
        return payment
    if payment.status == PaymentStatus.CAPTURED:
        return payment
    if payment.status in (PaymentStatus.FAILED, PaymentStatus.REFUNDED):
        raise PaymentServiceError("invalid_state", "Payment can no longer be captured.")
    if amount_paise is not None and int(amount_paise) != payment.amount_paise:
        raise PaymentServiceError("amount_mismatch", "Amount does not match the order.")

    payment.status = PaymentStatus.CAPTURED
    payment.razorpay_payment_id = razorpay_payment_id
    payment.save(update_fields=["status", "razorpay_payment_id", "updated_at"])
    Payout.objects.get_or_create(
        payment=payment,
        defaults={
            "coach": payment.coach,
            "amount_paise": payment.amount_paise,
            "status": PayoutStatus.DUE,
        },
    )
    _send_receipt(payment)
    return payment


@transaction.atomic
def fail_payment(*, order_id: str, razorpay_payment_id: str) -> Payment | None:
    payment = (
        Payment.objects.select_for_update().filter(razorpay_order_id=order_id).first()
    )
    if payment is None:
        return None
    if payment.status == PaymentStatus.CAPTURED:
        return payment
    if payment.status == PaymentStatus.FAILED and payment.razorpay_payment_id == razorpay_payment_id:
        return payment
    payment.status = PaymentStatus.FAILED
    payment.razorpay_payment_id = razorpay_payment_id
    payment.save(update_fields=["status", "razorpay_payment_id", "updated_at"])
    return payment


@transaction.atomic
def verify_checkout(user, hire_request_id, order_id: str, payment_id: str, signature: str) -> Payment:
    if not checkout_signature_ok(order_id, payment_id, signature):
        raise PaymentServiceError("invalid_signature", "Payment signature is invalid.")
    if not hasattr(user, "profile"):
        raise PaymentServiceError("forbidden", "Profile required.")
    try:
        hire_request = HireRequest.objects.get(pk=hire_request_id)
    except HireRequest.DoesNotExist:
        raise PaymentServiceError("not_found", "Hire request not found.")
    if user.profile.pk != hire_request.hirer_id:
        raise PaymentServiceError("forbidden", "Only the hirer can confirm this payment.")
    payment = Payment.objects.filter(
        hire_request=hire_request, razorpay_order_id=order_id
    ).first()
    if payment is None:
        raise PaymentServiceError("not_found", "Order does not belong to this request.")
    return capture_payment(order_id=order_id, razorpay_payment_id=payment_id)


def mark_payout_paid(payout: Payout, staff_user, utr: str) -> Payout:
    reference = (utr or "").strip()
    if not reference:
        raise PaymentServiceError("validation_error", "UTR is required to mark a payout paid.")
    if payout.status != PayoutStatus.DUE:
        raise PaymentServiceError("invalid_state", "Only due payouts can be marked paid.")
    payout.status = PayoutStatus.PAID
    payout.utr = reference
    payout.paid_at = timezone.now()
    payout.marked_by = staff_user
    payout.save(update_fields=["status", "utr", "paid_at", "marked_by", "updated_at"])
    return payout
