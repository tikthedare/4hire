import uuid

from django.db import models
from django.db.models import Q

from accounts.models import HirerKind, Profile
from listings.models import Listing


class HireRequestStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    DECLINED = "declined", "Declined"
    WITHDRAWN = "withdrawn", "Withdrawn"


class HireRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hirer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="hire_requests_sent"
    )
    coach = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="hire_requests_received"
    )
    listing = models.ForeignKey(Listing, on_delete=models.PROTECT, related_name="hire_requests")
    snapshot_hirer_kind = models.CharField(max_length=10, choices=HirerKind.choices)
    snapshot_club_name = models.CharField(max_length=120, null=True, blank=True)
    message = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=HireRequestStatus.choices,
        default=HireRequestStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach", "status"], name="hire_requests_coach_status_idx"),
            models.Index(fields=["hirer", "status"], name="hire_requests_hirer_status_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~Q(hirer_id=models.F("coach_id")),
                name="hire_requests_no_self",
            ),
            models.CheckConstraint(
                condition=(
                    Q(snapshot_hirer_kind=HirerKind.CLUB, snapshot_club_name__isnull=False)
                    | ~Q(snapshot_hirer_kind=HirerKind.CLUB)
                ),
                name="hire_requests_snapshot_club",
            ),
            models.UniqueConstraint(
                fields=["hirer", "coach"],
                condition=Q(status=HireRequestStatus.PENDING),
                name="hire_requests_one_pending_per_pair",
            ),
        ]
