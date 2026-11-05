"""
Credit Wallet & Ledger system for KSGP Video Platform
Immutable financial ledger design
"""
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
from apps.core.models import TimeStampedModel
from apps.core.blockchain import append_block
from apps.users.models import User
import uuid


class CreditWallet(TimeStampedModel):
    """Internal advertising credit wallet - not withdrawable currency"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    reserved = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    lifetime_purchased = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    lifetime_spent = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='EUR')
    is_locked = models.BooleanField(default=False)
    lock_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _('Credit Wallet')
        verbose_name_plural = _('Credit Wallets')

    def __str__(self):
        return f'Wallet of {self.user.email}: {self.balance} {self.currency}'

    @property
    def available_balance(self):
        return self.balance - self.reserved

    def can_reserve(self, amount):
        if self.is_locked:
            return False
        return self.available_balance >= amount

    @transaction.atomic
    def reserve(self, amount, campaign, description=''):
        """Reserve credits for a campaign. Atomic and ledgered."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        wallet = CreditWallet.objects.select_for_update().get(pk=self.pk)
        if not wallet.can_reserve(amount):
            raise ValidationError('Insufficient available balance')
        wallet.reserved += amount
        wallet.save(update_fields=['reserved', 'updated_at'])
        CreditTransaction.objects.create(
            wallet=wallet,
            transaction_type=CreditTransaction.Type.RESERVATION,
            amount=-amount,
            balance_after=wallet.balance,
            reserved_after=wallet.reserved,
            campaign=campaign,
            description=description or f'Reserved for campaign {campaign.name}',
            idempotency_key=f'reserve-{campaign.uuid}-{uuid.uuid4()}',
        )
        return True

    @transaction.atomic
    def release_reservation(self, amount, campaign, description=''):
        """Release reserved amount back to available"""
        wallet = CreditWallet.objects.select_for_update().get(pk=self.pk)
        release = min(amount, wallet.reserved)
        wallet.reserved -= release
        wallet.save(update_fields=['reserved', 'updated_at'])
        CreditTransaction.objects.create(
            wallet=wallet,
            transaction_type=CreditTransaction.Type.RELEASE,
            amount=release,
            balance_after=wallet.balance,
            reserved_after=wallet.reserved,
            campaign=campaign,
            description=description or f'Released reservation for {campaign.name}',
            idempotency_key=f'release-{campaign.uuid}-{uuid.uuid4()}',
        )
        return release

    @transaction.atomic
    def charge(self, amount, campaign, description='', idempotency_key=None):
        """Charge from reserved or balance. Prevents double spending."""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        wallet = CreditWallet.objects.select_for_update().get(pk=self.pk)
        if wallet.is_locked:
            raise ValidationError('Wallet is locked')
        if idempotency_key:
            existing = CreditTransaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
        from_reserved = min(amount, wallet.reserved)
        from_balance = amount - from_reserved
        if from_balance > wallet.balance - wallet.reserved + from_reserved:
            if wallet.available_balance + from_reserved < amount:
                raise ValidationError('Insufficient funds')
        wallet.reserved -= from_reserved
        wallet.balance -= amount
        wallet.lifetime_spent += amount
        if wallet.balance < 0:
            raise ValidationError('Balance cannot go negative')
        wallet.save(update_fields=['balance', 'reserved', 'lifetime_spent', 'updated_at'])
        tx = CreditTransaction.objects.create(
            wallet=wallet,
            transaction_type=CreditTransaction.Type.CHARGE,
            amount=-amount,
            balance_after=wallet.balance,
            reserved_after=wallet.reserved,
            campaign=campaign,
            description=description or f'Charge for campaign {campaign.name}',
            idempotency_key=idempotency_key or f'charge-{campaign.uuid}-{uuid.uuid4()}',
        )
        try:
            append_block(
                'credit_charge',
                actor=wallet.user,
                payload={'amount': str(amount), 'campaign_id': getattr(campaign, 'pk', None), 'balance_after': str(wallet.balance)},
                object_type='Campaign',
                object_id=getattr(campaign, 'pk', ''),
            )
        except Exception:
            pass
        return tx

    @transaction.atomic
    def credit(self, amount, description='', source='purchase', idempotency_key=None, payment=None):
        """Add credits (purchase or refund)"""
        if amount <= 0:
            raise ValidationError('Amount must be positive')
        wallet = CreditWallet.objects.select_for_update().get(pk=self.pk)
        if idempotency_key:
            existing = CreditTransaction.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                return existing
        wallet.balance += amount
        if source == 'purchase':
            wallet.lifetime_purchased += amount
        wallet.save(update_fields=['balance', 'lifetime_purchased', 'updated_at'])
        tx_type = CreditTransaction.Type.PURCHASE if source == 'purchase' else CreditTransaction.Type.REFUND
        tx = CreditTransaction.objects.create(
            wallet=wallet,
            transaction_type=tx_type,
            amount=amount,
            balance_after=wallet.balance,
            reserved_after=wallet.reserved,
            description=description,
            idempotency_key=idempotency_key or f'{source}-{uuid.uuid4()}',
            payment=payment,
        )
        try:
            append_block(
                'credit_wallet',
                actor=wallet.user,
                payload={'amount': str(amount), 'source': source, 'balance_after': str(wallet.balance)},
                object_type='CreditWallet',
                object_id=wallet.pk,
            )
        except Exception:
            pass
        return tx


class CreditTransaction(models.Model):
    """Immutable ledger of all credit movements"""
    class Type(models.TextChoices):
        PURCHASE = 'purchase', _('Credit Purchase')
        RESERVATION = 'reservation', _('Campaign Reservation')
        RELEASE = 'release', _('Reservation Release')
        CHARGE = 'charge', _('Campaign Charge')
        REFUND = 'refund', _('Refund')
        ADJUSTMENT = 'adjustment', _('Administrative Adjustment')
        EXPIRY = 'expiry', _('Credit Expiry')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(CreditWallet, on_delete=models.PROTECT, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=Type.choices, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)  # positive = credit, negative = debit
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reserved_after = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    campaign = models.ForeignKey('campaigns.Campaign', null=True, blank=True, on_delete=models.SET_NULL)
    payment = models.ForeignKey('payments.Payment', null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=255)
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Credit Transaction')
        verbose_name_plural = _('Credit Transactions')
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['transaction_type', 'created_at']),
        ]

    def __str__(self):
        return f'{self.get_transaction_type_display()}: {self.amount} @ {self.created_at}'

    def save(self, *args, **kwargs):
        # UUID primary keys are assigned before the first save. Therefore pk
        # cannot distinguish a new ledger row from an existing one.
        # _state.adding is True only until the first successful database insert.
        if not self._state.adding:
            raise ValidationError('Credit transactions are immutable and cannot be modified')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Credit transactions cannot be deleted')


class CreditPackage(TimeStampedModel):
    """Purchasable credit packages"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    credits = models.DecimalField(max_digits=12, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    bonus_credits = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    validity_days = models.PositiveIntegerField(null=True, blank=True, help_text='Null = never expires')
    max_campaigns = models.PositiveIntegerField(null=True, blank=True)
    features = models.JSONField(default=list, blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['order', 'price']

    def __str__(self):
        return f'{self.name}: {self.credits} credits for {self.price} {self.currency}'

    @property
    def total_credits(self):
        return self.credits + self.bonus_credits
