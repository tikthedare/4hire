from hire_requests.models import HireRequest, HireRequestStatus


def can_view_contact(viewer, other_profile) -> bool:
    """Counterparty PII only when an accepted hire request links the two profiles."""
    if viewer is None or not viewer.is_authenticated:
        return False
    if not hasattr(viewer, "profile"):
        return False
    me = viewer.profile
    if me.pk == other_profile.pk:
        return True
    return HireRequest.objects.filter(
        status=HireRequestStatus.ACCEPTED,
    ).filter(
        models_q_hirer_coach_pair(me.pk, other_profile.pk)
    ).exists()


def models_q_hirer_coach_pair(a, b):
    from django.db.models import Q

    return (Q(hirer_id=a, coach_id=b) | Q(hirer_id=b, coach_id=a))
