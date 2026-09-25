from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from payments.models import Payment, Payout, PayoutStatus
from payments.services import PaymentServiceError, mark_payout_paid


class PayoutAdminForm(forms.ModelForm):
    class Meta:
        model = Payout
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == PayoutStatus.PAID and not (cleaned.get("utr") or "").strip():
            raise forms.ValidationError("UTR is required to mark a payout paid.")
        return cleaned


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "status",
        "amount_paise",
        "currency",
        "hirer",
        "coach",
        "razorpay_order_id",
    )
    list_filter = ("status",)
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "hirer__display_name", "coach__display_name")
    readonly_fields = (
        "hire_request",
        "hirer",
        "coach",
        "amount_paise",
        "currency",
        "status",
        "razorpay_order_id",
        "razorpay_payment_id",
        "rate_rupees",
        "rate_unit",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    form = PayoutAdminForm
    list_display = ("created_at", "coach", "amount_paise", "status", "utr", "paid_at")
    list_filter = ("status",)
    search_fields = ("coach__display_name", "utr")
    readonly_fields = (
        "payment",
        "coach",
        "amount_paise",
        "paid_at",
        "marked_by",
        "created_at",
        "updated_at",
    )
    actions = ("mark_paid",)

    def has_add_permission(self, request):
        return False

    @admin.action(description="Mark selected payouts paid")
    def mark_paid(self, request, queryset):
        due = queryset.filter(status=PayoutStatus.DUE)
        utr = (request.POST.get("utr") or "").strip()
        if request.POST.get("apply"):
            if not utr:
                return self._mark_paid_form(request, due, error=True)
            updated = 0
            for payout in due:
                try:
                    mark_payout_paid(payout, request.user, utr)
                    updated += 1
                except PaymentServiceError as exc:
                    self.message_user(request, exc.detail, level=messages.ERROR)
            self.message_user(request, f"Marked {updated} payout(s) paid.")
            return HttpResponseRedirect(reverse("admin:payments_payout_changelist"))
        if not due.exists():
            self.message_user(
                request,
                "Select at least one due payout.",
                level=messages.ERROR,
            )
            return None
        return self._mark_paid_form(request, due, error=False)

    def _mark_paid_form(self, request, queryset, error: bool):
        context = {
            **self.admin_site.each_context(request),
            "title": "Mark payouts paid",
            "queryset": queryset,
            "opts": self.model._meta,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
            "utr_error": error,
        }
        return render(request, "admin/payments/mark_paid.html", context)

    def save_model(self, request, obj, form, change):
        if obj.status == PayoutStatus.PAID and obj.marked_by_id is None:
            obj.marked_by = request.user
        if obj.status == PayoutStatus.PAID and obj.paid_at is None:
            obj.paid_at = timezone.now()
        super().save_model(request, obj, form, change)
