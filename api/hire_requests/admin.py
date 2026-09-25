from django.contrib import admin

from hire_requests.models import HireRequest


@admin.register(HireRequest)
class HireRequestAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "hirer", "coach", "listing")
    list_filter = ("status",)
    search_fields = ("hirer__display_name", "coach__display_name", "message")
    readonly_fields = ("id", "created_at", "updated_at")
