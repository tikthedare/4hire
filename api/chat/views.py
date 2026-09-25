from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.throttles import MessageCreateThrottle
from chat.models import Message
from chat.serializers import MessageCreateSerializer, MessageSerializer
from chat.services import (
    ChatServiceError,
    assert_thread_open,
    load_party_request,
    parse_after,
)


def _error_status(code: str) -> int:
    if code == "forbidden":
        return status.HTTP_403_FORBIDDEN
    if code == "not_found":
        return status.HTTP_404_NOT_FOUND
    return status.HTTP_400_BAD_REQUEST


class HireMessageListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.request.method == "POST":
            return [MessageCreateThrottle()]
        return []

    def get(self, request, pk):
        try:
            hire_request = load_party_request(request.user, pk)
            after = parse_after(request.query_params.get("after"))
        except ChatServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        qs = Message.objects.filter(hire_request=hire_request).select_related("sender")
        if after is not None:
            qs = qs.filter(created_at__gt=after)
        return Response(MessageSerializer(qs, many=True).data)

    def post(self, request, pk):
        ser = MessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            hire_request = load_party_request(request.user, pk)
            assert_thread_open(hire_request)
        except ChatServiceError as exc:
            return Response(
                {"code": exc.code, "detail": exc.detail},
                status=_error_status(exc.code),
            )
        message = Message.objects.create(
            hire_request=hire_request,
            sender=request.user.profile,
            body=ser.validated_data["body"],
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)
