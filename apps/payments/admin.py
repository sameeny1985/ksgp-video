from django.contrib import admin
from .models import Payment, Invoice, Refund, Subscription


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'status', 'credits_granted', 'created_at')
    list_filter = ('status', 'payment_method', 'currency')
    search_fields = ('user__email', 'stripe_payment_intent_id', 'invoice_number')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'payment', 'issued_at')
    search_fields = ('invoice_number',)


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'payment', 'amount', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'status', 'price', 'interval', 'current_period_end')
    list_filter = ('status', 'interval')
    search_fields = ('user__email', 'plan_name')
