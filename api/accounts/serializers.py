from rest_framework import serializers

from accounts.models import Profile, UserRole
from accounts.permissions import can_view_contact
from common import validators
from common.validators import whatsapp_url


class CoachPublicSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)

    class Meta:
        model = Profile
        fields = ("id", "display_name")


class ProfileContactSerializer(serializers.ModelSerializer):
    whatsapp_url = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ("email", "mobile", "whatsapp_url")

    def get_whatsapp_url(self, obj):
        return whatsapp_url(obj.mobile)


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "role",
            "display_name",
            "email",
            "mobile",
            "hirer_kind",
            "club_name",
        )
        read_only_fields = ("email",)

    def validate_display_name(self, value):
        if err := validators.validate_display_name(value):
            raise serializers.ValidationError(err)
        return value.strip()

    def validate_mobile(self, value):
        if err := validators.validate_mobile(value):
            raise serializers.ValidationError(err)
        return value.strip()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=UserRole.choices)
    display_name = serializers.CharField()
    mobile = serializers.CharField()
    hirer_kind = serializers.ChoiceField(
        choices=[("player", "Player"), ("parent", "Parent"), ("club", "Club")],
        required=False,
        allow_null=True,
    )
    club_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class MeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "role",
            "display_name",
            "email",
            "mobile",
            "hirer_kind",
            "club_name",
        )


def serialize_counterparty(request, profile: Profile) -> dict:
    data = CoachPublicSerializer(profile).data
    if can_view_contact(request.user, profile):
        data.update(ProfileContactSerializer(profile).data)
    return data
