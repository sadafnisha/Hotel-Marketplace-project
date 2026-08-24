from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    The `api` app is a thin REST layer on top of the existing Django apps
    (accounts, listings, offers, chat). It intentionally contains NO models
    of its own -- it only exposes the existing models via DRF serializers,
    views and permissions, so there is a single source of truth for data
    and business rules.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'REST API'
