import pytest
from django.contrib.auth import get_user_model

from accounts.models import Profile, UserRole
from catalog.models import CoachRole, Sport
from listings.models import Listing

User = get_user_model()


@pytest.fixture
def soccer(db):
    sport, _ = Sport.objects.get_or_create(slug="soccer", defaults={"name": "Soccer"})
    roles = []
    for slug, name in [
        ("head-coach", "Head coach"),
        ("assistant", "Assistant coach"),
        ("goalkeeper", "Goalkeeper coach"),
        ("youth", "Youth coach"),
        ("fitness", "Fitness coach"),
    ]:
        role, _ = CoachRole.objects.get_or_create(
            sport=sport, slug=slug, defaults={"name": name}
        )
        roles.append(role)
    return sport, roles


def _make_user(email, role, **profile_kw):
    user = User.objects.create_user(email=email, password="testpass123")
    defaults = {
        "display_name": profile_kw.pop("display_name", "Test User"),
        "email": email,
        "mobile": profile_kw.pop("mobile", "9876543210"),
        "role": role,
    }
    if role == UserRole.HIRER:
        defaults.setdefault("hirer_kind", "player")
    Profile.objects.create(user=user, **defaults, **profile_kw)
    return user


@pytest.fixture
def coach_user(db):
    return _make_user("coach@test.local", UserRole.COACH, display_name="Coach One")


@pytest.fixture
def coach2_user(db):
    return _make_user(
        "coach2@test.local", UserRole.COACH, display_name="Coach Two", mobile="9988776655"
    )


@pytest.fixture
def hirer_user(db):
    return _make_user("hirer@test.local", UserRole.HIRER, display_name="Hirer One", mobile="9123456789")


@pytest.fixture
def coach_listing(coach_user, soccer):
    sport, _ = soccer
    return Listing.objects.create(
        coach=coach_user.profile,
        sport=sport,
        years_experience=5,
        city="Mumbai",
        remote_ok=False,
        rate_rupees=1500,
        rate_unit="session",
        available=True,
        bio="Test coach listing.",
    )
