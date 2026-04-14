from django.apps import AppConfig


class WalletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.wallet'
    verbose_name = 'Wallet'

    def ready(self):
        # Auto-create wallet for every new user via signal
        import Apps.wallet.signals  # noqa: F401
