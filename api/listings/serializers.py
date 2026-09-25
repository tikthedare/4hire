from rest_framework import serializers

from accounts.models import Profile, UserRole
from accounts.serializers import CoachPublicSerializer
from catalog.models import CoachRole, Sport
from common import validators
from listings.models import Listing, ListingRole


class CoachRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoachRole
        fields = ("id", "slug", "name")


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ("id", "slug", "name")


class ListingSummarySerializer(serializers.ModelSerializer):
    coach = CoachPublicSerializer(read_only=True)
    coach_role_slugs = serializers.SerializerMethodField()
    sport_slug = serializers.CharField(source="sport.slug", read_only=True)
    rating_avg = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id",
            "coach",
            "sport_slug",
            "years_experience",
            "city",
            "remote_ok",
            "rate_rupees",
            "rate_unit",
            "available",
            "bio",
            "coach_role_slugs",
            "rating_avg",
            "rating_count",
        )

    def get_rating_avg(self, obj):
        if obj.rating_avg is None:
            return None
        return float(obj.rating_avg)

    def get_coach_role_slugs(self, obj):
        return list(
            obj.listing_roles.select_related("coach_role").values_list(
                "coach_role__slug", flat=True
            )
        )


class CoachDirectorySerializer(ListingSummarySerializer):
    """Public directory card — no contact fields."""


class CoachDetailSerializer(ListingSummarySerializer):
    """Public coach detail — no contact fields."""


class ListingWriteSerializer(serializers.ModelSerializer):
    coach_role_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = Listing
        fields = (
            "years_experience",
            "city",
            "remote_ok",
            "rate_rupees",
            "rate_unit",
            "available",
            "bio",
            "coach_role_ids",
        )

    def validate(self, attrs):
        for field, fn in (
            ("bio", validators.validate_bio),
            ("city", validators.validate_city),
            ("years_experience", validators.validate_years_experience),
            ("rate_rupees", validators.validate_rate_rupees),
        ):
            if field in attrs:
                err = fn(attrs[field])
                if err:
                    raise serializers.ValidationError({field: err})
        return attrs

    def _sync_roles(self, listing, role_ids):
        ListingRole.objects.filter(listing=listing).delete()
        if role_ids:
            roles = CoachRole.objects.filter(id__in=role_ids)
            for role in roles:
                ListingRole.objects.create(listing=listing, coach_role=role)

    def create(self, validated_data):
        role_ids = validated_data.pop("coach_role_ids", [])
        profile = self.context["request"].user.profile
        from catalog.models import Sport

        sport = Sport.objects.get(slug="soccer")
        listing = Listing.objects.create(coach=profile, sport=sport, **validated_data)
        self._sync_roles(listing, role_ids)
        return listing

    def update(self, instance, validated_data):
        role_ids = validated_data.pop("coach_role_ids", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if role_ids is not None:
            self._sync_roles(instance, role_ids)
        return instance


class ListingReadSerializer(ListingSummarySerializer):
    coach_role_ids = serializers.SerializerMethodField()

    class Meta(ListingSummarySerializer.Meta):
        fields = ListingSummarySerializer.Meta.fields + ("coach_role_ids",)

    def get_coach_role_ids(self, obj):
        return list(obj.listing_roles.values_list("coach_role_id", flat=True))
