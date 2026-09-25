import base64
import json
import urllib.error
import urllib.request

from django.conf import settings


class RazorpayError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


def create_razorpay_order(*, amount_paise: int, receipt: str, notes: dict) -> dict:
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        raise RazorpayError("Razorpay is not configured.")
    payload = json.dumps(
        {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt[:40],
            "notes": {k: str(v) for k, v in notes.items()},
        }
    ).encode()
    token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    request = urllib.request.Request(
        "https://api.razorpay.com/v1/orders",
        data=payload,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise RazorpayError("Could not create Razorpay order.") from exc
    except urllib.error.URLError as exc:
        raise RazorpayError("Could not reach Razorpay.") from exc
