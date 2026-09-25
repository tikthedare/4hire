import hashlib
import hmac
import json

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from accounts.models import Profile, UserRole
from hire_requests.models import HireRequest, HireRequestStatus
from payments.models import Payment, PaymentStatus, Payout, PayoutStatus
from payments.services import PaymentServiceError, mark_payout_paid
from reviews.models import Review

User = get_user_model()


@pytest.fixture
def api():
    return APIClient()


def _auth(client, user):
    client.force_authenticate(user=user)


def _hire(hirer, coach, listing, status=HireRequestStatus.PENDING):
    return HireRequest.objects.create(
        hirer=hirer.profile,
        coach=coach.profile,
        listing=listing,
        snapshot_hirer_kind="player",
        message="Please coach our team.",
        status=status,
    )


def _capture(hire_request, suffix):
    hire_request.status = HireRequestStatus.ACCEPTED
    hire_request.save(update_fields=["status", "updated_at"])
    return Payment.objects.create(
        hire_request=hire_request,
        hirer=hire_request.hirer,
        coach=hire_request.coach,
        amount_paise=hire_request.listing.rate_rupees * 100,
        currency="INR",
        status=PaymentStatus.CAPTURED,
        razorpay_order_id=f"order_{suffix}",
        razorpay_payment_id=f"pay_{suffix}",
        rate_rupees=hire_request.listing.rate_rupees,
        rate_unit=hire_request.listing.rate_unit,
    )


def _webhook(client, payload, signature=None):
    raw = json.dumps(payload)
    if signature is None:
        signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            raw.encode(),
            hashlib.sha256,
        ).hexdigest()
    return client.post(
        "/api/v1/payments/webhook/",
        data=raw,
        content_type="application/json",
        HTTP_X_RAZORPAY_SIGNATURE=signature,
    )


def _captured_event(order_id, payment_id, amount):
    return {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": payment_id,
                    "order_id": order_id,
                    "amount": amount,
                    "currency": "INR",
                    "status": "captured",
                }
            }
        },
    }


@pytest.mark.django_db
def test_hirer_cannot_pay_pending_request(api, hirer_user, coach_user, coach_listing, monkeypatch):
    hire_request = _hire(hirer_user, coach_user, coach_listing)

    def explode(**kwargs):
        raise AssertionError("Razorpay should not be called")

    monkeypatch.setattr("payments.services.create_razorpay_order", explode)
    _auth(api, hirer_user)
    res = api.post(f"/api/v1/hire-requests/{hire_request.id}/payments/order/")
    assert res.status_code == 400
    assert res.data["code"] == "invalid_state"
    assert Payment.objects.count() == 0


@pytest.mark.django_db
def test_webhook_signature_and_replay(api, hirer_user, coach_user, coach_listing, monkeypatch):
    hire_request = _hire(hirer_user, coach_user, coach_listing, status=HireRequestStatus.ACCEPTED)
    monkeypatch.setattr(
        "payments.services.create_razorpay_order",
        lambda **kwargs: {"id": "order_scale_1"},
    )
    _auth(api, hirer_user)
    created = api.post(f"/api/v1/hire-requests/{hire_request.id}/payments/order/")
    assert created.status_code == 201
    assert created.data["order_id"] == "order_scale_1"
    assert created.data["key_id"] == "rzp_test_key"
    assert created.data["amount_paise"] == coach_listing.rate_rupees * 100
    assert "razorpay_payment_id" not in created.data

    again = api.post(f"/api/v1/hire-requests/{hire_request.id}/payments/order/")
    assert again.status_code == 200
    assert again.data["order_id"] == "order_scale_1"
    assert Payment.objects.count() == 1

    event = _captured_event("order_scale_1", "pay_scale_1", coach_listing.rate_rupees * 100)
    rejected = _webhook(api, event, signature="not-a-valid-signature")
    assert rejected.status_code == 400
    payment = Payment.objects.get()
    assert payment.status == PaymentStatus.CREATED
    assert Payout.objects.count() == 0

    captured = _webhook(api, event)
    assert captured.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.CAPTURED
    assert payment.razorpay_payment_id == "pay_scale_1"
    assert Payout.objects.count() == 1
    payout = Payout.objects.get()
    assert payout.amount_paise == payment.amount_paise
    assert payout.status == PayoutStatus.DUE

    replay = _webhook(api, event)
    assert replay.status_code == 200
    payment.refresh_from_db()
    assert payment.status == PaymentStatus.CAPTURED
    assert Payout.objects.count() == 1

    api.force_authenticate(user=hirer_user)
    mine = api.get("/api/v1/me/payments/")
    assert mine.status_code == 200
    assert mine.data[0]["status"] == "captured"
    assert "razorpay_order_id" not in mine.data[0]
    assert "razorpay_payment_id" not in mine.data[0]


@pytest.mark.django_db
def test_messages_are_party_only_and_closed_when_declined(
    api, hirer_user, coach_user, coach2_user, coach_listing
):
    hire_request = _hire(hirer_user, coach_user, coach_listing)
    _auth(api, coach2_user)
    denied = api.get(f"/api/v1/hire-requests/{hire_request.id}/messages/")
    assert denied.status_code == 403

    _auth(api, hirer_user)
    posted = api.post(
        f"/api/v1/hire-requests/{hire_request.id}/messages/",
        {"body": "Can we start Saturday?"},
        format="json",
    )
    assert posted.status_code == 201
    assert posted.data["sender_display_name"] == hirer_user.profile.display_name
    assert "email" not in posted.data

    hire_request.status = HireRequestStatus.DECLINED
    hire_request.save(update_fields=["status", "updated_at"])

    listed = api.get(f"/api/v1/hire-requests/{hire_request.id}/messages/")
    assert listed.status_code == 200
    assert len(listed.data) == 1

    closed = api.post(
        f"/api/v1/hire-requests/{hire_request.id}/messages/",
        {"body": "One more note"},
        format="json",
    )
    assert closed.status_code == 400
    assert closed.data["code"] == "invalid_state"


@pytest.mark.django_db
def test_one_review_and_hidden_reviews_leave_the_public_average(
    api, hirer_user, coach_user, coach_listing
):
    other = User.objects.create_user(email="hirer2@test.local", password="testpass123")
    Profile.objects.create(
        user=other,
        role=UserRole.HIRER,
        display_name="Second Hirer",
        email="hirer2@test.local",
        mobile="9000000001",
        hirer_kind="player",
    )
    first = _hire(hirer_user, coach_user, coach_listing)
    second = _hire(other, coach_user, coach_listing)
    _capture(first, "rev1")
    _capture(second, "rev2")

    _auth(api, hirer_user)
    missing_payment = HireRequest.objects.create(
        hirer=hirer_user.profile,
        coach=coach_user.profile,
        listing=coach_listing,
        snapshot_hirer_kind="player",
        message="Unpaid follow up.",
        status=HireRequestStatus.ACCEPTED,
    )
    unpaid = api.post(
        f"/api/v1/hire-requests/{missing_payment.id}/review/",
        {"rating": 5, "body": "Should fail"},
        format="json",
    )
    assert unpaid.status_code == 400

    created = api.post(
        f"/api/v1/hire-requests/{first.id}/review/",
        {"rating": 5, "body": "Excellent session"},
        format="json",
    )
    assert created.status_code == 201
    assert created.data["hirer_display_name"] == "Hirer One"
    assert "email" not in created.data
    assert "mobile" not in created.data

    duplicate = api.post(
        f"/api/v1/hire-requests/{first.id}/review/",
        {"rating": 4, "body": "Changed my mind"},
        format="json",
    )
    assert duplicate.status_code == 400

    _auth(api, other)
    second_review = api.post(
        f"/api/v1/hire-requests/{second.id}/review/",
        {"rating": 1, "body": "secret-low-score"},
        format="json",
    )
    assert second_review.status_code == 201

    public = api.get(f"/api/v1/coaches/{coach_user.profile.pk}/reviews/")
    assert public.status_code == 200
    assert public.data["rating_count"] == 2
    assert public.data["rating_avg"] == pytest.approx(3.0)

    low = Review.objects.get(hire_request=second)
    low.hidden = True
    low.save(update_fields=["hidden"])

    directory = api.get("/api/v1/coaches/")
    assert directory.status_code == 200
    card = directory.data[0]
    assert card["rating_count"] == 1
    assert card["rating_avg"] == pytest.approx(5.0)
    blob = json.dumps(directory.data)
    assert coach_user.profile.email not in blob
    assert coach_user.profile.mobile not in blob
    assert "email" not in card["coach"]
    assert "mobile" not in card["coach"]

    visible = api.get(f"/api/v1/coaches/{coach_user.profile.pk}/reviews/")
    visible_blob = json.dumps(visible.data)
    assert visible.data["rating_count"] == 1
    assert "secret-low-score" not in visible_blob
    assert hirer_user.profile.email not in visible_blob
    assert hirer_user.profile.mobile not in visible_blob
    assert visible.data["reviews"][0]["hirer_display_name"] == "Hirer One"


@pytest.mark.django_db
def test_mark_payout_paid_requires_utr(hirer_user, coach_user, coach_listing):
    hire_request = _hire(hirer_user, coach_user, coach_listing)
    payment = _capture(hire_request, "payout1")
    payout = Payout.objects.create(
        payment=payment,
        coach=coach_user.profile,
        amount_paise=payment.amount_paise,
        status=PayoutStatus.DUE,
    )
    with pytest.raises(PaymentServiceError):
        mark_payout_paid(payout, hirer_user, " ")
    mark_payout_paid(payout, hirer_user, "123456789012")
    payout.refresh_from_db()
    assert payout.status == PayoutStatus.PAID
    assert payout.utr == "123456789012"
    assert payout.marked_by_id == hirer_user.pk
    assert payout.paid_at is not None
