from django.db import IntegrityError, transaction

from accounts.models import Profile, UserRole
from common import validators
from common.exceptions import PENDING_PAIR_MESSAGE
from hire_requests.models import HireRequest, HireRequestStatus
from listings.models import Listing


class HireRequestServiceError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


@transaction.atomic
def create_hire_request(hirer_user, listing_id, message: str) -> HireRequest:
    if not hasattr(hirer_user, "profile"):
        raise HireRequestServiceError("forbidden", "Profile required.")
    profile = hirer_user.profile
    if profile.role != UserRole.HIRER or not profile.hirer_kind:
        raise HireRequestServiceError("forbidden", "Only hirers can send requests.")

    if err := validators.validate_message(message):
        raise HireRequestServiceError("validation_error", err)

    try:
        listing = Listing.objects.select_related("coach").get(pk=listing_id)
    except Listing.DoesNotExist:
        raise HireRequestServiceError("not_found", "Listing not found.")

    if not listing.available:
        raise HireRequestServiceError("unavailable", "This coach is not available.")
    if listing.coach_id == profile.pk:
        raise HireRequestServiceError("forbidden", "You cannot request yourself.")

    try:
        return HireRequest.objects.create(
            hirer=profile,
            coach=listing.coach,
            listing=listing,
            snapshot_hirer_kind=profile.hirer_kind,
            snapshot_club_name=profile.club_name if profile.hirer_kind == "club" else None,
            message=message.strip(),
            status=HireRequestStatus.PENDING,
        )
    except IntegrityError:
        raise HireRequestServiceError("pending_pair_exists", PENDING_PAIR_MESSAGE)


@transaction.atomic
def transition_hire_request(hire_request: HireRequest, actor_user, new_status: str) -> HireRequest:
    if not hasattr(actor_user, "profile"):
        raise HireRequestServiceError("forbidden", "Profile required.")
    profile = actor_user.profile
    role = "coach" if profile.pk == hire_request.coach_id else "hirer"
    if profile.pk not in (hire_request.coach_id, hire_request.hirer_id):
        raise HireRequestServiceError("forbidden", "Not a party on this request.")

    if not validators.can_transition_hire_request_status(
        hire_request.status, new_status, role
    ):
        raise HireRequestServiceError("invalid_transition", "Status change not allowed.")

    hire_request.status = new_status
    hire_request.save(update_fields=["status", "updated_at"])
    return hire_request
