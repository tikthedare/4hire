from rest_framework import generics
from rest_framework.permissions import AllowAny

from catalog.models import CoachRole, Sport
from listings.serializers import CoachRoleSerializer, SportSerializer


class SportListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Sport.objects.all()
    serializer_class = SportSerializer


class CoachRoleListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CoachRoleSerializer

    def get_queryset(self):
        qs = CoachRole.objects.select_related("sport")
        sport = self.request.query_params.get("sport")
        if sport:
            qs = qs.filter(sport__slug=sport)
        return qs
