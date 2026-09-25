from django.db import transaction

from accounts.models import Profile, User, UserRole
from common import validators


class RegistrationError(Exception):
    def __init__(self, errors: dict):
        self.errors = errors
        super().__init__(str(errors))


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    role: str,
    display_name: str,
    mobile: str,
    hirer_kind: str | None = None,
    club_name: str | None = None,
) -> User:
    errors: dict[str, str] = {}
    if err := validators.validate_display_name(display_name):
        errors["display_name"] = err
    if err := validators.validate_mobile(mobile):
        errors["mobile"] = err
    if role == UserRole.HIRER:
        if not hirer_kind:
            errors["hirer_kind"] = "Hirer kind is required."
        if err := validators.validate_club_name(hirer_kind, club_name):
            errors["club_name"] = err
    elif role == UserRole.COACH:
        hirer_kind = None
        club_name = None
    else:
        errors["role"] = "Invalid role."

    if errors:
        raise RegistrationError(errors)

    user = User.objects.create_user(email=email, password=password)
    Profile.objects.create(
        user=user,
        role=role,
        display_name=display_name.strip(),
        email=user.email,
        mobile=mobile.strip(),
        hirer_kind=hirer_kind if role == UserRole.HIRER else None,
        club_name=club_name.strip() if hirer_kind == "club" and club_name else None,
    )
    return user
