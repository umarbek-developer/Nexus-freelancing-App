from django.apps import AppConfig


class ProposalsConfig(AppConfig):
    name = 'Apps.proposals'

    def ready(self):
        import Apps.proposals.signals  # noqa: F401 — registers email signals
