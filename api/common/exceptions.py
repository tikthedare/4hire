from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


PENDING_PAIR_MESSAGE = (
    "You already have a pending request with this coach. "
    "Check your inbox or withdraw it first."
)


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict):
        if "detail" in response.data and "code" not in response.data:
            response.data = {"code": "error", "detail": response.data["detail"]}
        elif "detail" not in response.data:
            response.data = {"code": "validation_error", "detail": response.data}
    if response is None and isinstance(exc, IntegrityError):
        msg = str(exc)
        if "hire_requests_one_pending_per_pair" in msg or "unique" in msg.lower():
            return Response(
                {"code": "pending_pair_exists", "detail": PENDING_PAIR_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST,
            )
    return response
