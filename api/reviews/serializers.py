from rest_framework import serializers

from reviews.models import Review


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    body = serializers.CharField(min_length=1, max_length=500, trim_whitespace=True)


class ReviewPublicSerializer(serializers.ModelSerializer):
    hirer_display_name = serializers.CharField(source="hirer.display_name", read_only=True)

    class Meta:
        model = Review
        fields = ("id", "rating", "body", "created_at", "hirer_display_name")
