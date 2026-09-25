"""Ensure the Django admin Staff group exists after migrations."""

STAFF_PERMISSIONS = (
    "view_user",
    "change_user",
    "view_profile",
    "change_profile",
    "view_listing",
    "change_listing",
    "view_hirerequest",
    "change_hirerequest",
    "view_payment",
    "view_payout",
    "change_payout",
    "view_review",
    "change_review",
    "view_message",
)


def ensure_staff_group(sender, **kwargs):
    from django.contrib.auth.models import Group, Permission
    from django.db.utils import OperationalError, ProgrammingError

    try:
        group, _ = Group.objects.get_or_create(name="Staff")
        perms = Permission.objects.filter(codename__in=STAFF_PERMISSIONS)
        if perms.exists():
            group.permissions.add(*perms)
    except (OperationalError, ProgrammingError):
        return
