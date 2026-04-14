"""
Contract completed → email freelancer with payment confirmation (#8).
"""
import logging

from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Contract

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Contract)
def on_contract_save(sender, instance, created, **kwargs):
    contract = instance
    if not created and contract.status == 'completed':
        email = contract.freelancer.email
        if email:
            try:
                send_mail(
                    subject='To\'lov amalga oshirildi — The Nexus',
                    message=(
                        f'Salom {contract.freelancer.username},\n\n'
                        f'"{contract.job.title}" bo\'yicha shartnoma yakunlandi.\n'
                        f'${contract.amount} hisobingizga o\'tkazildi.\n\n'
                        f'Hamyoningizni tekshirish uchun saytga kiring.\n\n'
                        f'— The Nexus jamoasi'
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as exc:
                logger.error(
                    'Contract completed email failed: contract=%s error=%s',
                    contract.pk, exc,
                )
            else:
                logger.info(
                    'Contract completed email sent: contract=%s freelancer=%s',
                    contract.pk, contract.freelancer_id,
                )
