"""
Email notification signals — Feature #8.

Signals fire on:
  1. Proposal created  → email to job's client
  2. Proposal accepted → email to freelancer
  3. Contract completed (in contracts/signals.py) → email to freelancer
"""
import logging

from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Proposal

logger = logging.getLogger(__name__)


def _send(subject, body, recipients):
    """Safe wrapper — logs failures instead of crashing the request."""
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[r for r in recipients if r],
            fail_silently=False,
        )
    except Exception as exc:
        logger.error('Email send failed: subject=%s error=%s', subject, exc)


@receiver(post_save, sender=Proposal)
def on_proposal_save(sender, instance, created, **kwargs):
    proposal = instance

    # ── 1. New proposal → notify client ─────────────────────────────────────
    if created:
        client_email = proposal.job.client.email
        if client_email:
            _send(
                subject=f'Yangi taklif: {proposal.job.title}',
                body=(
                    f'Salom {proposal.job.client.username},\n\n'
                    f'{proposal.freelancer.username} sizning "{proposal.job.title}" '
                    f'ishingizga taklif yubordi.\n\n'
                    f'Taklif narxi: ${proposal.proposed_rate}\n\n'
                    f'Taklifni ko\'rish uchun saytga kiring.\n\n'
                    f'— The Nexus jamoasi'
                ),
                recipients=[client_email],
            )
        logger.info(
            'Proposal created email sent: proposal=%s client=%s',
            proposal.pk, proposal.job.client_id,
        )

    # ── 2. Proposal accepted → notify freelancer ─────────────────────────────
    elif proposal.status == Proposal.ACCEPTED:
        freelancer_email = proposal.freelancer.email
        if freelancer_email:
            _send(
                subject=f'Tabriklaymiz! Taklifingiz qabul qilindi',
                body=(
                    f'Salom {proposal.freelancer.username},\n\n'
                    f'"{proposal.job.title}" ishi uchun taklifingiz qabul qilindi!\n\n'
                    f'Shartnoma yaratildi. Ish boshlashingiz mumkin.\n\n'
                    f'— The Nexus jamoasi'
                ),
                recipients=[freelancer_email],
            )
        logger.info(
            'Proposal accepted email sent: proposal=%s freelancer=%s',
            proposal.pk, proposal.freelancer_id,
        )
