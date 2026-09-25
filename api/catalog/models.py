import uuid

from django.db import models


class Sport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CoachRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name="coach_roles")
    slug = models.SlugField()
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sport", "slug"], name="coach_roles_sport_slug_uniq"),
        ]

    def __str__(self):
        return self.name
