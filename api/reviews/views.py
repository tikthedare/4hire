from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserRole
from accounts.throttles import ReviewCreateThrottle
from hire_requests.models import HireRequest, HireRequestStatus
from listings.models import Listing
from payments.models import PaymentStatus
from reviews.serializers import ReviewCreateSerializer, ReviewPublicSerializer
from reviews.services import ReviewServiceError, create_review


def _error_status(code: str) -> int:
    if code == "forbidden":
        return status.HTTP_403_FORBIDDEN
    if code == "not_found":
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_400_BAD_REQUEST


class HireReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ReviewCreateThrottle]

    def post(self, request, pk):
        ser = ReviewCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            review = create_review(
                request.user,
                pk,
                ser.validated_data["rating"],
                ser.validated_data["body"],
            )
        except ReviewServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        return Response(
            ReviewPublicSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class CoachReviewsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        listing = Listing.objects.filter(coach_id=id, available=True).first()
        if not listing:
            return Response(
                {"code": "not_found", "detail": "Coach not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        from reviews.models import Review

        reviews = (
            Review.objects.filter(coach_id=id, hidden=False)
            .select_related("hirer")
            .order_by("-created_at")[:20]
        )
        eligible = None
        user = request.user
        if user.is_authenticated and hasattr(user, "profile") and user.profile.role == UserRole.HIRER:
            match = (
                HireRequest.objects.filter(
                    hirer=user.profile,
                    coach_id=id,
                    status=HireRequestStatus.ACCEPTED,
                    payments__status=PaymentStatus.CAPTURED,
                    review__isnull=True,
                )
                .order_by("-updated_at")
                .first()
            )
            if match:
                eligible = str(match.id)
        avg = float(listing.rating_avg) if listing.rating_avg is not None else None
        return Response(
            {
                "rating_avg": avg,
                "rating_count": listing.rating_count,
                "eligible_hire_request_id": eligible,
                "reviews": ReviewPublicSerializer(reviews, many=True).data,
            }
        )
