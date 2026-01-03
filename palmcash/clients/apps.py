from django.apps import AppConfig


class ClientsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clients'
    verbose_name = 'Client Management'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import clients.signals  # noqa
