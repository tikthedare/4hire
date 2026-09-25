import pytest
from rest_framework.test import APIClient

from accounts.models import Profile, UserRole
from hire_requests.models import HireRequest, HireRequestStatus


@pytest.fixture
def api():
    return APIClient()


def _auth(client, user):
    client.force_authenticate(user=user)


def test_directory_hides_contact(api, coach_listing):
    res = api.get("/api/v1/coaches/")
    assert res.status_code == 200
    coach = res.data[0]["coach"]
    assert "display_name" in coach
    assert "email" not in coach
    assert "mobile" not in coach


def test_hirer_cannot_create_listing(api, hirer_user, soccer):
    _auth(api, hirer_user)
    res = api.put(
        "/api/v1/me/listing/",
        {
            "years_experience": 3,
            "city": "Mumbai",
            "remote_ok": False,
            "rate_rupees": 1000,
            "rate_unit": "session",
            "available": True,
            "bio": "Should fail.",
        },
        format="json",
    )
    assert res.status_code == 403


def test_coach_cannot_patch_other_listing(api, coach_user, coach2_user, soccer, coach_listing):
    sport, _ = soccer
    from listings.models import Listing

    Listing.objects.create(
        coach=coach2_user.profile,
        sport=sport,
        years_experience=2,
        city="Pune",
        rate_rupees=800,
        rate_unit="session",
        bio="Other coach.",
    )
    _auth(api, coach2_user)
    res = api.put(
        "/api/v1/me/listing/",
        {
            "years_experience": 99,
            "city": "Hacked",
            "remote_ok": False,
            "rate_rupees": 1000,
            "rate_unit": "session",
            "available": True,
            "bio": "Only updates own listing.",
        },
        format="json",
    )
    listing = Listing.objects.get(coach=coach2_user.profile)
    assert listing.city == "Pune"
    assert listing.years_experience == 2


def test_contact_only_when_accepted(api, coach_user, hirer_user, coach_listing):
    hr = HireRequest.objects.create(
        hirer=hirer_user.profile,
        coach=coach_user.profile,
        listing=coach_listing,
        snapshot_hirer_kind="player",
        message="Hello coach.",
        status=HireRequestStatus.PENDING,
    )
    _auth(api, hirer_user)
    res = api.get("/api/v1/me/requests/?box=sent")
    counterparty = res.data[0]["counterparty"]
    assert "mobile" not in counterparty
    assert "email" not in counterparty

    hr.status = HireRequestStatus.ACCEPTED
    hr.save()
    res = api.get("/api/v1/me/requests/?box=sent")
    counterparty = res.data[0]["counterparty"]
    assert counterparty.get("mobile") == coach_user.profile.mobile
    assert "whatsapp_url" in counterparty


def test_role_immutable(api, hirer_user):
    _auth(api, hirer_user)
    res = api.patch(
        "/api/v1/me/",
        {"role": "coach", "display_name": hirer_user.profile.display_name},
        format="json",
    )
    assert res.status_code == 200
    hirer_user.profile.refresh_from_db()
    assert hirer_user.profile.role == UserRole.HIRER
