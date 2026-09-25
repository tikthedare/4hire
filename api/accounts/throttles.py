from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class RegisterThrottle(AnonRateThrottle):
    scope = "auth_register"


class HireRequestCreateThrottle(UserRateThrottle):
    scope = "hire_request_create"


class MessageCreateThrottle(UserRateThrottle):
    scope = "message_create"


class ReviewCreateThrottle(UserRateThrottle):
    scope = "review_create"
