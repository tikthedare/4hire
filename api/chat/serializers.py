from rest_framework import serializers

from chat.models import Message


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.UUIDField(read_only=True)
    sender_display_name = serializers.CharField(source="sender.display_name", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender_id", "sender_display_name", "body", "created_at")
