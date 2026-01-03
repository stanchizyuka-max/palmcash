from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loans'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import loans.signals  # noqa