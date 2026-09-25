from django.utils import timezone
from django.utils.dateparse import parse_datetime

from hire_requests.models import HireRequest, HireRequestStatus


OPEN_STATUSES = {HireRequestStatus.PENDING, HireRequestStatus.ACCEPTED}


class ChatServiceError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


def load_party_request(user, hire_request_id) -> HireRequest:
    if not hasattr(user, "profile"):
        raise ChatServiceError("forbidden", "Profile required.")
    try:
        hire_request = HireRequest.objects.get(pk=hire_request_id)
    except HireRequest.DoesNotExist:
        raise ChatServiceError("not_found", "Hire request not found.")
    profile = user.profile
    if profile.pk not in (hire_request.hirer_id, hire_request.coach_id):
        raise ChatServiceError("forbidden", "Only parties on this hire can view messages.")
    return hire_request


def parse_after(raw: str | None):
    if not raw:
        return None
    parsed = parse_datetime(raw)
    if parsed is None:
        raise ChatServiceError("validation_error", "Invalid after timestamp.")
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def assert_thread_open(hire_request: HireRequest):
    if hire_request.status not in OPEN_STATUSES:
        raise ChatServiceError(
            "invalid_state",
            "Messages are closed once a request is declined or withdrawn.",
        )
