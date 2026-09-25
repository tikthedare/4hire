import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from accounts.models import Profile
from hire_requests.models import HireRequest
from listings.models import RateUnit


class PaymentStatus(models.TextChoices):
    CREATED = "created", "Created"
    AUTHORIZED = "authorized", "Authorized"
    CAPTURED = "captured", "Captured"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PayoutStatus(models.TextChoices):
    DUE = "due", "Due"
    PAID = "paid", "Paid"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hire_request = models.ForeignKey(
        HireRequest, on_delete=models.PROTECT, related_name="payments"
    )
    hirer = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name="payments_made"
    )
    coach = models.ForeignKey(
        Profile, on_delete=models.PROTECT, related_name="payments_received"
    )
    amount_paise = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="INR")
    status = models.CharField(
        max_length=12, choices=PaymentStatus.choices, default=PaymentStatus.CREATED
    )
    razorpay_order_id = models.CharField(max_length=40, unique=True)
    razorpay_payment_id = models.CharField(max_length=40, unique=True, null=True, blank=True)
    rate_rupees = models.PositiveIntegerField()
    rate_unit = models.CharField(max_length=10, choices=RateUnit.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["hirer", "created_at"], name="payments_hirer_created_idx"),
            models.Index(fields=["coach", "status"], name="payments_coach_status_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["hire_request"],
                condition=~Q(status=PaymentStatus.FAILED),
                name="payments_one_active_per_hire",
            ),
            models.CheckConstraint(
                condition=Q(amount_paise__gt=0),
                name="payments_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(currency="INR"),
                name="payments_currency_inr",
            ),
        ]

    def __str__(self):
        return f"{self.status} {self.amount_paise} paise"


class Payout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="payout")
    coach = models.ForeignKey(Profile, on_delete=models.PROTECT, related_name="payouts")
    amount_paise = models.PositiveIntegerField()
    status = models.CharField(
        max_length=8, choices=PayoutStatus.choices, default=PayoutStatus.DUE
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    utr = models.CharField(max_length=64, blank=True, default="")
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payouts_marked",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_paise__gt=0),
                name="payouts_amount_positive",
            ),
        ]

    def __str__(self):
        return f"{self.status} {self.amount_paise} paise"
