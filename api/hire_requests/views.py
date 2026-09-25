from django.db.models import Prefetch
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.throttles import HireRequestCreateThrottle
from hire_requests.models import HireRequest
from payments.models import Payment, PaymentStatus
from hire_requests.serializers import (
    HireRequestCreateSerializer,
    HireRequestSerializer,
    HireRequestStatusSerializer,
)
from hire_requests.services import HireRequestServiceError, create_hire_request, transition_hire_request


class HireRequestCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [HireRequestCreateThrottle]

    def post(self, request):
        ser = HireRequestCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            hr = create_hire_request(
                request.user,
                ser.validated_data["listing_id"],
                ser.validated_data["message"],
            )
        except HireRequestServiceError as exc:
            code = status.HTTP_403_FORBIDDEN if exc.code == "forbidden" else status.HTTP_400_BAD_REQUEST
            if exc.code == "not_found":
                code = status.HTTP_404_NOT_FOUND
            return Response({"code": exc.code, "detail": exc.detail}, status=code)
        return Response(
            HireRequestSerializer(hr, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class HireRequestUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            hr = HireRequest.objects.get(pk=pk)
        except HireRequest.DoesNotExist:
            return Response(
                {"code": "not_found", "detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        ser = HireRequestStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            hr = transition_hire_request(hr, request.user, ser.validated_data["status"])
        except HireRequestServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=status.HTTP_403_FORBIDDEN
                if exc.code == "forbidden"
                else status.HTTP_400_BAD_REQUEST,
            )
        return Response(HireRequestSerializer(hr, context={"request": request}).data)


class MyRequestsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HireRequestSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        box = self.request.query_params.get("box", "sent")
        qs = HireRequest.objects.select_related("hirer", "coach", "listing").prefetch_related(
            "review",
            Prefetch(
                "payments",
                queryset=Payment.objects.exclude(status=PaymentStatus.FAILED).order_by(
                    "-created_at"
                ),
                to_attr="open_payments",
            ),
        )
        if box == "incoming":
            return qs.filter(coach=profile)
        return qs.filter(hirer=profile)
