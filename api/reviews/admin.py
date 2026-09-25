from django.contrib import admin

from reviews.models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("created_at", "coach", "hirer", "rating", "hidden")
    list_filter = ("hidden", "rating")
    search_fields = ("body", "hirer__display_name", "coach__display_name")
    readonly_fields = ("hire_request", "coach", "hirer", "rating", "body", "created_at")
    actions = ("hide_reviews", "unhide_reviews")

    @admin.action(description="Hide selected reviews")
    def hide_reviews(self, request, queryset):
        for review in queryset:
            if not review.hidden:
                review.hidden = True
                review.save(update_fields=["hidden"])

    @admin.action(description="Restore selected reviews")
    def unhide_reviews(self, request, queryset):
        for review in queryset:
            if review.hidden:
                review.hidden = False
                review.save(update_fields=["hidden"])

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from reviews.aggregates import refresh_listing_ratings

        refresh_listing_ratings(obj.coach_id)
