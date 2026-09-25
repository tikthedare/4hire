from django.db import IntegrityError, transaction

from accounts.models import UserRole
from hire_requests.models import HireRequest, HireRequestStatus
from payments.models import Payment, PaymentStatus
from reviews.models import Review


class ReviewServiceError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


@transaction.atomic
def create_review(user, hire_request_id, rating: int, body: str) -> Review:
    if not hasattr(user, "profile"):
        raise ReviewServiceError("forbidden", "Profile required.")
    profile = user.profile
    if profile.role != UserRole.HIRER:
        raise ReviewServiceError("forbidden", "Only hirers can leave a review.")

    try:
        hire_request = HireRequest.objects.select_related("coach", "hirer").get(pk=hire_request_id)
    except HireRequest.DoesNotExist:
        raise ReviewServiceError("not_found", "Hire request not found.")

    if profile.pk != hire_request.hirer_id:
        raise ReviewServiceError("forbidden", "Only the hirer on this request can review.")
    if hire_request.status != HireRequestStatus.ACCEPTED:
        raise ReviewServiceError("invalid_state", "You can review only an accepted hire.")
    captured = Payment.objects.filter(
        hire_request=hire_request, status=PaymentStatus.CAPTURED
    ).exists()
    if not captured:
        raise ReviewServiceError(
            "invalid_state", "You can review only after payment is captured."
        )

    text = body.strip()
    if not text or len(text) > 500:
        raise ReviewServiceError("validation_error", "Review text must be 1–500 characters.")
    if rating < 1 or rating > 5:
        raise ReviewServiceError("validation_error", "Rating must be from 1 to 5.")

    try:
        return Review.objects.create(
            hire_request=hire_request,
            coach=hire_request.coach,
            hirer=profile,
            rating=rating,
            body=text,
        )
    except IntegrityError:
        raise ReviewServiceError("already_reviewed", "This hire already has a review.")
