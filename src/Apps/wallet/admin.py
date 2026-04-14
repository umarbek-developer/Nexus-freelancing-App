from django.contrib import admin
from .models import Wallet, Transaction


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ('amount', 'transaction_type', 'description', 'created_at')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display  = ('user', 'balance', 'updated_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TransactionInline]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ('wallet', 'transaction_type', 'amount', 'description', 'created_at')
    list_filter   = ('transaction_type',)
    search_fields = ('wallet__user__username', 'description')
    readonly_fields = ('wallet', 'amount', 'transaction_type', 'description', 'created_at')

    def has_add_permission(self, request):
        return False  # Transactions are immutable — created only via code

    def has_change_permission(self, request, obj=None):
        return False
