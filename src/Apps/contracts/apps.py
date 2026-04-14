from django.apps import AppConfig


class ContractsConfig(AppConfig):
    name = 'Apps.contracts'

    def ready(self):
        import Apps.contracts.signals  # noqa: F401 — registers email signals
