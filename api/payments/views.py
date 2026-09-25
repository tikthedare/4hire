import json

from django.conf import settings
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from payments.models import Payment
from payments.services import (
    PaymentServiceError,
    create_payment_order,
    fail_payment,
    verify_checkout,
    webhook_signature_ok,
    capture_payment,
)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "hire_request_id",
            "amount_paise",
            "currency",
            "status",
            "rate_rupees",
            "rate_unit",
            "created_at",
        )


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


def _error_status(code: str) -> int:
    if code == "forbidden":
        return status.HTTP_403_FORBIDDEN
    if code == "not_found":
        return status.HTTP_404_NOT_FOUND
    if code == "not_configured":
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if code == "gateway_error":
        return status.HTTP_502_BAD_GATEWAY
    return status.HTTP_400_BAD_REQUEST


def _order_payload(payment: Payment) -> dict:
    return {
        "order_id": payment.razorpay_order_id,
        "key_id": settings.RAZORPAY_KEY_ID,
        "amount_paise": payment.amount_paise,
        "currency": payment.currency,
        "status": payment.status,
    }


class HirePaymentOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            payment, created = create_payment_order(request.user, pk)
        except PaymentServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        return Response(
            _order_payload(payment),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class HirePaymentVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        ser = VerifyPaymentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            payment = verify_checkout(
                request.user,
                pk,
                ser.validated_data["razorpay_order_id"],
                ser.validated_data["razorpay_payment_id"],
                ser.validated_data["razorpay_signature"],
            )
        except PaymentServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        return Response(PaymentSerializer(payment).data)


class MyPaymentsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        profile = self.request.user.profile
        return (
            Payment.objects.filter(Q(hirer=profile) | Q(coach=profile))
            .distinct()
            .order_by("-created_at")
        )


class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        raw = request.body
        signature = request.headers.get("X-Razorpay-Signature", "")
        if not webhook_signature_ok(raw, signature):
            return Response(
                {"code": "invalid_signature", "detail": "Invalid signature."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            event = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return Response(
                {"code": "validation_error", "detail": "Invalid JSON."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        name = event.get("event")
        entity = (
            event.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        if name not in ("payment.captured", "payment.failed") or not order_id or not payment_id:
            return Response({"status": "ignored"})
        try:
            if name == "payment.captured":
                capture_payment(
                    order_id=order_id,
                    razorpay_payment_id=payment_id,
                    amount_paise=entity.get("amount"),
                )
            else:
                fail_payment(order_id=order_id, razorpay_payment_id=payment_id)
        except PaymentServiceError as exc:
            if exc.code == "not_found":
                return Response({"status": "ignored"})
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        return Response({"status": "ok"})
