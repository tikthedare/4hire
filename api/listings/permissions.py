from rest_framework.permissions import BasePermission

from accounts.models import UserRole


class IsCoach(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and hasattr(request.user, "profile")
            and request.user.profile.role == UserRole.COACH
        )


class IsListingOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            hasattr(request.user, "profile")
            and obj.coach_id == request.user.profile.pk
        )
