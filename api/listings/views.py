from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from listings.models import Listing
from listings.permissions import IsCoach
from listings.serializers import (
    CoachDetailSerializer,
    CoachDirectorySerializer,
    ListingReadSerializer,
    ListingWriteSerializer,
)


class CoachDirectoryView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = CoachDirectorySerializer

    def get_queryset(self):
        qs = (
            Listing.objects.filter(available=True)
            .select_related("coach", "sport")
            .prefetch_related("listing_roles__coach_role")
        )
        coach_role = self.request.query_params.get("coach_role")
        if coach_role:
            qs = qs.filter(listing_roles__coach_role__slug=coach_role)
        city = self.request.query_params.get("city")
        if city:
            qs = qs.filter(city__icontains=city.strip())
        remote = self.request.query_params.get("remote")
        if remote in ("true", "1"):
            qs = qs.filter(remote_ok=True)
        return qs.distinct()


class CoachDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = CoachDetailSerializer
    lookup_field = "coach_id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Listing.objects.filter(available=True).select_related(
            "coach", "sport"
        ).prefetch_related("listing_roles__coach_role")


class MyListingView(APIView):
    permission_classes = [IsAuthenticated, IsCoach]

    def get(self, request):
        listing = Listing.objects.filter(coach=request.user.profile).first()
        if not listing:
            return Response(
                {"code": "not_found", "detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ListingReadSerializer(listing).data)

    def put(self, request):
        profile = request.user.profile
        listing = Listing.objects.filter(coach=profile).first()
        if listing:
            ser = ListingWriteSerializer(
                listing, data=request.data, context={"request": request}
            )
        else:
            ser = ListingWriteSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        saved = ser.save()
        return Response(ListingReadSerializer(saved).data)
