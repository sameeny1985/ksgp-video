"""
Payment models with Stripe integration for KSGP Video
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from apps.core.models import TimeStampedModel
from apps.users.models import User
import uuid


class Payment(TimeStampedModel):
    """Payment record"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        SUCCEEDED = 'succeeded', _('Succeeded')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')

    class PaymentMethod(models.TextChoices):
        STRIPE = 'stripe', _('Stripe')
        OTHER = 'other', _('Other')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payments')
    package = models.ForeignKey('credits.CreditPackage', null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.STRIPE)
    
    # Stripe
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, db_index=True)
    stripe_checkout_session_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_charge_id = models.CharField(max_length=100, blank=True)
    
    # Credits granted
    credits_granted = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    credits_granted_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    description = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    receipt_url = models.URLField(blank=True)
    invoice_number = models.CharField(max_length=50, blank=True, unique=True, null=True)
    
    # Idempotency
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f'Payment {self.id} - {self.amount} {self.currency} ({self.status})'


class Invoice(TimeStampedModel):
    """Generated invoices"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    pdf_file = models.FileField(upload_to='invoices/%Y/%m/', blank=True, null=True)
    billing_name = models.CharField(max_length=200, blank=True)
    billing_address = models.TextField(blank=True)
    billing_email = models.EmailField(blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.invoice_number


class Refund(TimeStampedModel):
    """Refund records"""
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SUCCEEDED = 'succeeded', _('Succeeded')
        FAILED = 'failed', _('Failed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField(blank=True)
    stripe_refund_id = models.CharField(max_length=100, blank=True)
    credits_revoked = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    processed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    processed_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Refund {self.amount} for payment {self.payment_id}'


class Subscription(TimeStampedModel):
    """Optional subscription plans"""
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        CANCELLED = 'cancelled', _('Cancelled')
        EXPIRED = 'expired', _('Expired')
        PAST_DUE = 'past_due', _('Past Due')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    interval = models.CharField(max_length=20, choices=[('month', 'Monthly'), ('year', 'Yearly')])
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    features = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - {self.plan_name} ({self.status})'
