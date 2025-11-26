from django.apps import AppConfig


class DemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "demo"

    def ready(self):
        """
        Import custom blocks when Django starts.

        This ensures that blocks decorated with @register_common_block
        are registered before the StreamField definitions are loaded.
        """
        try:
            import demo.blocks  # noqa: F401
        except ImportError:
            pass
