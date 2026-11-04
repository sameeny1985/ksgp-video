from django.contrib import admin
from .models import CreditWallet, CreditTransaction, CreditPackage


@admin.register(CreditWallet)
class CreditWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'reserved', 'available_balance', 'lifetime_purchased', 'lifetime_spent', 'is_locked')
    list_filter = ('is_locked', 'currency')
    search_fields = ('user__email',)
    readonly_fields = ('lifetime_purchased', 'lifetime_spent', 'created_at', 'updated_at')


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'balance_after', 'campaign', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('wallet__user__email', 'idempotency_key', 'description')
    readonly_fields = [f.name for f in CreditTransaction._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(CreditPackage)
class CreditPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'credits', 'bonus_credits', 'price', 'currency', 'is_active', 'is_featured', 'order')
    list_editable = ('is_active', 'is_featured', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
