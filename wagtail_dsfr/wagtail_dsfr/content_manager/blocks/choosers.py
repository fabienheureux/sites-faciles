"""
Custom ChooserBlock implementations that support swappable models.
Similar to ImageChooserBlock pattern in Wagtail.
"""
from django.utils.functional import cached_property
from wagtail.blocks import PageChooserBlock


class BlogIndexChooserBlock(PageChooserBlock):
    """
    A PageChooserBlock that automatically uses the configured blog index model.
    """

    @cached_property
    def target_model(self):
        from wagtail_dsfr.utils.models import get_blog_index_model

        return get_blog_index_model()


class EventsIndexChooserBlock(PageChooserBlock):
    """
    A PageChooserBlock that automatically uses the configured events index model.
    """

    @cached_property
    def target_model(self):
        from wagtail_dsfr.utils.models import get_events_index_model

        return get_events_index_model()
