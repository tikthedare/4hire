from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.jwt import EmailTokenObtainPairSerializer


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer
