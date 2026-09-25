import uuid

from django.db import models

from accounts.models import Profile
from hire_requests.models import HireRequest


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hire_request = models.ForeignKey(
        HireRequest, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="chat_messages")
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["hire_request", "created_at"], name="chat_message_thread_idx"),
        ]

    def __str__(self):
        return f"Message {self.id}"
