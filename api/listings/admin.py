from django.contrib import admin

from listings.models import Listing, ListingRole


class ListingRoleInline(admin.TabularInline):
    model = ListingRole
    extra = 0


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "coach",
        "city",
        "rate_rupees",
        "rate_unit",
        "available",
        "rating_avg",
        "rating_count",
    )
    list_filter = ("available", "city", "rate_unit")
    search_fields = ("coach__display_name", "city")
    readonly_fields = ("rating_avg", "rating_count", "created_at", "updated_at")
    inlines = [ListingRoleInline]
