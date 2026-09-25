import pytest

from common.validators import (
    can_transition_hire_request_status,
    validate_bio,
    validate_message,
    validate_mobile,
    validate_rate_rupees,
    whatsapp_url,
)


@pytest.mark.parametrize(
    "mobile,ok",
    [
        ("9876543210", True),
        ("6123456789", True),
        ("5876543210", False),
        ("987654321", False),
        ("98765432101", False),
    ],
)
def test_validate_mobile(mobile, ok):
    assert (validate_mobile(mobile) is None) == ok


def test_validate_bio_length():
    assert validate_bio("") is not None
    assert validate_bio("a" * 501) is not None
    assert validate_bio("Experienced coach in Mumbai.") is None


def test_validate_message_length():
    assert validate_message("") is not None
    assert validate_message("x" * 1001) is not None
    assert validate_message("Looking for weekend sessions.") is None


def test_validate_rate_rupees():
    assert validate_rate_rupees(0) is not None
    assert validate_rate_rupees(-100) is not None
    assert validate_rate_rupees(1500) is None


def test_can_transition_hire_request_status():
    assert can_transition_hire_request_status("pending", "accepted", "coach")
    assert can_transition_hire_request_status("pending", "declined", "coach")
    assert not can_transition_hire_request_status("pending", "withdrawn", "coach")
    assert can_transition_hire_request_status("pending", "withdrawn", "hirer")
    assert not can_transition_hire_request_status("pending", "accepted", "hirer")
    assert not can_transition_hire_request_status("accepted", "withdrawn", "hirer")


def test_whatsapp_url():
    assert whatsapp_url("9876543210") == "https://wa.me/919876543210"
