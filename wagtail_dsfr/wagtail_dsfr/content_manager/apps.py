from django.apps import AppConfig


class ContentManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wagtail_dsfr.content_manager"
    label = "wagtail_dsfr_content_manager"

    def ready(self):
        """
        Extend STREAMFIELD_COMMON_BLOCKS with registered custom blocks.

        This is called after all apps are loaded, so custom blocks registered
        via @register_common_block decorator will be available.
        """
        from wagtail_dsfr.content_manager.blocks import core
        from wagtail_dsfr.content_manager.registry import get_registered_blocks

        registered_blocks = get_registered_blocks()
        if registered_blocks:
            core.STREAMFIELD_COMMON_BLOCKS.extend(registered_blocks)
