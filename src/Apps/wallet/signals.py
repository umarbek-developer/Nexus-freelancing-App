"""
Auto-create a Wallet for every new User.
This fires after user.save() on CREATE only.
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        from Apps.wallet.models import Wallet
        Wallet.objects.get_or_create(user=instance)
