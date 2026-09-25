from rest_framework import serializers

from accounts.serializers import serialize_counterparty
from hire_requests.models import HireRequest


class HireRequestCreateSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    message = serializers.CharField()


class HireRequestStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["accepted", "declined", "withdrawn"]
    )


class HireRequestSerializer(serializers.ModelSerializer):
    counterparty = serializers.SerializerMethodField()
    listing_id = serializers.UUIDField(source="listing.id", read_only=True)
    payment_status = serializers.SerializerMethodField()
    has_review = serializers.SerializerMethodField()

    class Meta:
        model = HireRequest
        fields = (
            "id",
            "listing_id",
            "message",
            "status",
            "snapshot_hirer_kind",
            "snapshot_club_name",
            "created_at",
            "updated_at",
            "counterparty",
            "payment_status",
            "has_review",
        )

    def get_counterparty(self, obj):
        request = self.context["request"]
        profile = request.user.profile
        other = obj.hirer if profile.pk == obj.coach_id else obj.coach
        return serialize_counterparty(request, other)

    def get_payment_status(self, obj):
        from payments.models import Payment, PaymentStatus

        prefetched = getattr(obj, "open_payments", None)
        if prefetched is not None:
            payment = prefetched[0] if prefetched else None
        else:
            payment = (
                Payment.objects.filter(hire_request=obj)
                .exclude(status=PaymentStatus.FAILED)
                .order_by("-created_at")
                .first()
            )
        return payment.status if payment else None

    def get_has_review(self, obj):
        from django.core.exceptions import ObjectDoesNotExist

        try:
            return obj.review is not None
        except ObjectDoesNotExist:
            return False
