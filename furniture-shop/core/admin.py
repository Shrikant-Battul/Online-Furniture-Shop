from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm
from django import forms
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price")
    list_filter = ("category",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "total", "payment_method", "status", "order_code", "created_at")
    list_filter = ("payment_method", "status", "created_at")
    search_fields = ("name", "email", "phone", "payment_reference", "order_code")
    inlines = [OrderItemInline]

    # Action form to accept a code for proceeding orders
    class ProceedActionForm(ActionForm):
        proceed_code = forms.CharField(required=False, label="Enter order code to proceed")

    action_form = ProceedActionForm

    actions = ["proceed_order", "mark_paid", "mark_cancelled"]

    def proceed_order(self, request, queryset):
        code = (request.POST.get('proceed_code') or '').strip().upper()
        if not code:
            self.message_user(request, "Please enter an order code in the action form.", level=messages.WARNING)
            return
        matched = queryset.filter(order_code__iexact=code)
        count = matched.update(status='paid')
        if count:
            self.message_user(request, f"Proceeded {count} order(s) with code {code}.", level=messages.SUCCESS)
        else:
            self.message_user(request, "No selected orders matched the provided code.", level=messages.WARNING)
    proceed_order.short_description = "Proceed Order (enter code to mark as Paid)"

    def mark_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f"Marked {updated} order(s) as paid.")
    mark_paid.short_description = "Mark selected orders as Paid"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"Cancelled {updated} order(s).")
    mark_cancelled.short_description = "Mark selected orders as Cancelled"

# Register your models here.
