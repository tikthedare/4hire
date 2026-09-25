import os

import dj_database_url

from .base import *  # noqa: F403

DEBUG = False

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

DATABASES = {
    "default": dj_database_url.config(
        default="sqlite://:memory:",
        conn_max_age=0,
    )
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["NAME"] = ":memory:"

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/hour",
        "user": "10000/hour",
        "auth_register": "10000/hour",
        "hire_request_create": "10000/hour",
        "message_create": "10000/hour",
        "review_create": "10000/hour",
    },
}

RAZORPAY_KEY_ID = "rzp_test_key"
RAZORPAY_KEY_SECRET = "test_secret"
RAZORPAY_WEBHOOK_SECRET = "whsec_test"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
