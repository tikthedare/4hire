import uuid

from django.db import models

from accounts.models import Profile
from hire_requests.models import HireRequest


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hire_request = models.OneToOneField(
        HireRequest, on_delete=models.CASCADE, related_name="review"
    )
    coach = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews_received"
    )
    hirer = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="reviews_written"
    )
    rating = models.PositiveSmallIntegerField()
    body = models.TextField()
    hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["coach"], name="reviews_coach_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="reviews_rating_range",
            ),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from reviews.aggregates import refresh_listing_ratings

        refresh_listing_ratings(self.coach_id)

    def delete(self, *args, **kwargs):
        coach_id = self.coach_id
        super().delete(*args, **kwargs)
        from reviews.aggregates import refresh_listing_ratings

        refresh_listing_ratings(coach_id)

    def __str__(self):
        return f"{self.rating}/5 for {self.coach_id}"
