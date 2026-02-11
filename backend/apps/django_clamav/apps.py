from django.apps import AppConfig


class DjangoClamavConfig(AppConfig):
    name = "django_clamav"
    verbose_name = "Django ClamAV"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Import conf to validate settings on startup
        from django_clamav import conf  # noqa: F401
