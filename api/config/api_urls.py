from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.jwt_views import EmailTokenObtainPairView
from accounts.views import LogoutView, MeView, RegisterView
from catalog.views import CoachRoleListView, SportListView
from chat.views import HireMessageListCreateView
from hire_requests.views import HireRequestCreateView, HireRequestUpdateView, MyRequestsView
from listings.views import CoachDetailView, CoachDirectoryView, MyListingView
from payments.views import (
    HirePaymentOrderView,
    HirePaymentVerifyView,
    MyPaymentsView,
    RazorpayWebhookView,
)
from reviews.views import CoachReviewsView, HireReviewCreateView

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/token/", EmailTokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("auth/logout/", LogoutView.as_view()),
    path("me/", MeView.as_view()),
    path("sports/", SportListView.as_view()),
    path("coach-roles/", CoachRoleListView.as_view()),
    path("coaches/", CoachDirectoryView.as_view()),
    path("coaches/<uuid:id>/", CoachDetailView.as_view()),
    path("coaches/<uuid:id>/reviews/", CoachReviewsView.as_view()),
    path("me/listing/", MyListingView.as_view()),
    path("me/requests/", MyRequestsView.as_view()),
    path("me/payments/", MyPaymentsView.as_view()),
    path("hire-requests/", HireRequestCreateView.as_view()),
    path("hire-requests/<uuid:pk>/", HireRequestUpdateView.as_view()),
    path("hire-requests/<uuid:pk>/payments/order/", HirePaymentOrderView.as_view()),
    path("hire-requests/<uuid:pk>/payments/verify/", HirePaymentVerifyView.as_view()),
    path("hire-requests/<uuid:pk>/messages/", HireMessageListCreateView.as_view()),
    path("hire-requests/<uuid:pk>/review/", HireReviewCreateView.as_view()),
    path("payments/webhook/", RazorpayWebhookView.as_view()),
]
