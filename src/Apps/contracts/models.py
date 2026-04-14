"""
Contract and Milestone models.

Contract  — one per accepted job.
Milestone — optional phase-based payments inside a contract (#15).
Dispute   — freelancer/client dispute on an active contract (#14).
"""
import logging
from decimal import Decimal

from django.db import models
from django.conf import settings

logger = logging.getLogger(__name__)


class Contract(models.Model):
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed',  'Disputed'),
    ]

    job        = models.OneToOneField('jobs.Job', on_delete=models.CASCADE)
    client     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='client_contracts')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='freelancer_contracts')
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    # #19: db_index on status — filtered in almost every dashboard query
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.job.title} — {self.status}'


# ── Feature #15: Milestone payments ──────────────────────────────────────────

class Milestone(models.Model):
    """
    Phase-based payment inside a contract.
    Each milestone has its own amount and can be released independently.
    Sum of all milestones should equal contract.amount.
    """
    PENDING   = 'pending'
    RELEASED  = 'released'
    STATUS_CHOICES = [(PENDING, 'Pending'), (RELEASED, 'Released')]

    contract    = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='milestones')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    due_date    = models.DateField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Milestone "{self.title}" — ${self.amount} [{self.status}]'


# ── Feature #14: Dispute system ───────────────────────────────────────────────

class Dispute(models.Model):
    """
    Either party can open a dispute on an active contract.
    Admin reviews and resolves it (approve/reject via admin panel).
    """
    OPEN     = 'open'
    RESOLVED = 'resolved'
    CLOSED   = 'closed'
    STATUS_CHOICES = [
        (OPEN,     'Open'),
        (RESOLVED, 'Resolved'),
        (CLOSED,   'Closed'),
    ]

    contract    = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='disputes')
    opened_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='disputes_opened')
    reason      = models.TextField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=OPEN, db_index=True)
    admin_note  = models.TextField(blank=True, help_text='Admin resolution notes')
    resolution  = models.CharField(
        max_length=30,
        blank=True,
        choices=[
            ('favour_client',     'Favour Client'),
            ('favour_freelancer', 'Favour Freelancer'),
            ('split',             'Split'),
        ],
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Dispute #{self.pk} on Contract #{self.contract_id} [{self.status}]'
