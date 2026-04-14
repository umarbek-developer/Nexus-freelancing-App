"""
Wallet, Transaction, and Withdrawal models.

Wallet  — one per user, stores available (realised) balance.
Transaction — immutable ledger; never update, only create.
Withdrawal  — tracks withdrawal requests (Feature #13).
"""
import logging
from decimal import Decimal

from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)


class Wallet(models.Model):
    user    = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'

    def __str__(self):
        return f'{self.user.username} — ${self.balance}'

    # ── Mutation helpers ──────────────────────────────────────────────────────

    def credit(self, amount, description=''):
        """Add funds. Call inside atomic block."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Credit amount must be positive.')
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
        tx = Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.CREDIT,
            description=description,
        )
        logger.info('Wallet credit: user=%s amount=%s tx=%s', self.user_id, amount, tx.pk)
        return tx

    def debit(self, amount, description=''):
        """Deduct funds. Call inside atomic block."""
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError('Debit amount must be positive.')
        if self.balance < amount:
            raise ValueError(f'Insufficient balance. Available: ${self.balance}')
        self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])
        tx = Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.DEBIT,
            description=description,
        )
        logger.info('Wallet debit: user=%s amount=%s tx=%s', self.user_id, amount, tx.pk)
        return tx


class Transaction(models.Model):
    """Immutable ledger entry. Never update — only create."""
    CREDIT = 'credit'
    DEBIT  = 'debit'
    TYPE_CHOICES = [(CREDIT, 'Credit'), (DEBIT, 'Debit')]

    wallet           = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount           = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description      = models.CharField(max_length=300, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.transaction_type == self.CREDIT else '-'
        return f'{sign}${self.amount} — {self.wallet.user.username}'


# ── Feature #13: Withdrawal system ───────────────────────────────────────────

class Withdrawal(models.Model):
    """
    Freelancer requests withdrawal of available wallet balance.
    Admin approves/rejects. On approval, wallet is debited.
    """
    PENDING  = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (PENDING,  'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    wallet      = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawals')
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    method      = models.CharField(
        max_length=30,
        choices=[
            ('bank_transfer', 'Bank Transfer'),
            ('paypal',        'PayPal'),
            ('crypto',        'Crypto'),
        ],
        default='bank_transfer',
    )
    # Destination details (store as plain text; real app would encrypt)
    destination = models.CharField(max_length=300, help_text='Bank account / PayPal / wallet address')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    note        = models.TextField(blank=True, help_text='Admin rejection note')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Withdrawal ${self.amount} — {self.wallet.user.username} [{self.status}]'
