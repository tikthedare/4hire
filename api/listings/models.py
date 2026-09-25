import uuid

from django.db import models

from accounts.models import Profile
from catalog.models import CoachRole, Sport


class RateUnit(models.TextChoices):
    SESSION = "session", "Session"
    MONTH = "month", "Month"


class Listing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    coach = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="listing"
    )
    sport = models.ForeignKey(Sport, on_delete=models.PROTECT, related_name="listings")
    years_experience = models.PositiveSmallIntegerField()
    city = models.CharField(max_length=80)
    remote_ok = models.BooleanField(default=False)
    rate_rupees = models.PositiveIntegerField()
    rate_unit = models.CharField(max_length=10, choices=RateUnit.choices)
    available = models.BooleanField(default=True)
    bio = models.TextField()
    rating_count = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["sport", "available"], name="listings_available_sport_idx"),
            models.Index(fields=["city"], name="listings_city_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(years_experience__gte=0, years_experience__lte=60),
                name="listings_years_check",
            ),
            models.CheckConstraint(
                condition=models.Q(rate_rupees__gt=0),
                name="listings_rate_check",
            ),
        ]


class ListingRole(models.Model):
    listing = models.ForeignKey(
        Listing, on_delete=models.CASCADE, related_name="listing_roles"
    )
    coach_role = models.ForeignKey(CoachRole, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "coach_role"], name="listing_roles_uniq"
            ),
        ]
