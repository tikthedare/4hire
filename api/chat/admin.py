from django.contrib import admin

from chat.models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("created_at", "hire_request", "sender", "body_preview")
    search_fields = ("body", "sender__display_name")
    readonly_fields = ("hire_request", "sender", "body", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="Body")
    def body_preview(self, obj):
        return obj.body[:80]
