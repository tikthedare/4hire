from django.contrib import admin

from accounts.models import Profile, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active", "created_at")
    search_fields = ("email",)
    list_filter = ("is_staff", "is_active")
    filter_horizontal = ("groups",)
    fields = (
        "id",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "groups",
        "last_login",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        readonly = ["id", "email", "last_login", "created_at", "updated_at"]
        if not request.user.is_superuser:
            readonly.extend(["is_active", "is_staff", "is_superuser", "groups"])
        return readonly

    def has_add_permission(self, request):
        return False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "role", "email", "mobile")
    search_fields = ("display_name", "email", "mobile")
    list_filter = ("role",)
    readonly_fields = ("user", "role", "email", "created_at", "updated_at")
    fields = (
        "user",
        "role",
        "display_name",
        "email",
        "mobile",
        "hirer_kind",
        "club_name",
        "created_at",
        "updated_at",
    )
