from django.apps import AppConfig


class ContentManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "{package_name}.content_manager"
    label = "{package_name}_content_manager"
