import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from common.validators import MOBILE_RE


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    def __str__(self):
        return self.email


class UserRole(models.TextChoices):
    HIRER = "hirer", "Hirer"
    COACH = "coach", "Coach"


class HirerKind(models.TextChoices):
    PLAYER = "player", "Player"
    PARENT = "parent", "Parent"
    CLUB = "club", "Club"


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True, related_name="profile"
    )
    role = models.CharField(max_length=10, choices=UserRole.choices)
    display_name = models.CharField(max_length=80)
    email = models.EmailField()
    mobile = models.CharField(max_length=10)
    hirer_kind = models.CharField(
        max_length=10, choices=HirerKind.choices, null=True, blank=True
    )
    club_name = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(role=UserRole.COACH, hirer_kind__isnull=True, club_name__isnull=True)
                    | models.Q(role=UserRole.HIRER, hirer_kind__isnull=False)
                ),
                name="profiles_hirer_kind_check",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(hirer_kind=HirerKind.CLUB, club_name__isnull=False)
                    | models.Q(hirer_kind__isnull=True)
                    | ~models.Q(hirer_kind=HirerKind.CLUB)
                ),
                name="profiles_club_name_check",
            ),
        ]

    def clean(self):
        if not MOBILE_RE.match(self.mobile):
            raise ValidationError({"mobile": "Invalid Indian mobile number."})
        if self.role == UserRole.COACH:
            if self.hirer_kind or self.club_name:
                raise ValidationError("Coaches cannot have hirer fields.")
        if self.role == UserRole.HIRER and not self.hirer_kind:
            raise ValidationError({"hirer_kind": "Required for hirers."})
        if self.hirer_kind == HirerKind.CLUB:
            if not self.club_name or not self.club_name.strip():
                raise ValidationError({"club_name": "Club name is required."})
        elif self.club_name:
            raise ValidationError({"club_name": "Only club hirers may set club name."})

    def save(self, *args, **kwargs):
        if self.pk:
            old = Profile.objects.filter(pk=self.pk).only("role").first()
            if old and old.role != self.role:
                raise ValidationError("Profile role cannot be changed.")
        self.full_clean()
        super().save(*args, **kwargs)
