import pytest
from django.core.exceptions import ValidationError

from accounts.models import Profile, User, UserRole
from hire_requests.models import HireRequest, HireRequestStatus

@pytest.mark.django_db
def test_profile_role_immutable(coach_user):
    profile = coach_user.profile
    profile.role = UserRole.HIRER
    with pytest.raises(ValidationError):
        profile.save()


@pytest.mark.django_db
def test_one_pending_hire_request_per_pair(coach_user, hirer_user, coach_listing):
    HireRequest.objects.create(
        hirer=hirer_user.profile,
        coach=coach_user.profile,
        listing=coach_listing,
        snapshot_hirer_kind="player",
        message="First",
        status=HireRequestStatus.PENDING,
    )
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        HireRequest.objects.create(
            hirer=hirer_user.profile,
            coach=coach_user.profile,
            listing=coach_listing,
            snapshot_hirer_kind="player",
            message="Second",
            status=HireRequestStatus.PENDING,
        )
