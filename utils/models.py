"""
Helper functions to get swappable model references.
Similar to Wagtail's get_image_model() pattern.
"""

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_blog_index_model_string():
    """
    Get the dotted ``app.Model`` name for the blog index model as a string.
    """
    return getattr(
        settings,
        "WAGTAIL_DSFR_BLOG_INDEX_MODEL",
        "wagtail_dsfr_blog.BlogIndexPage",
    )


def get_blog_index_model():
    """
    Get the blog index model from the ``WAGTAIL_DSFR_BLOG_INDEX_MODEL`` setting.
    Defaults to the standard ``wagtail_dsfr.blog.models.BlogIndexPage`` model
    if no custom model is defined.
    """
    model_string = get_blog_index_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "WAGTAIL_DSFR_BLOG_INDEX_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"WAGTAIL_DSFR_BLOG_INDEX_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_blog_entry_model_string():
    """
    Get the dotted ``app.Model`` name for the blog entry model as a string.
    """
    return getattr(
        settings,
        "WAGTAIL_DSFR_BLOG_ENTRY_MODEL",
        "wagtail_dsfr_blog.BlogEntryPage",
    )


def get_blog_entry_model():
    """
    Get the blog entry model from the ``WAGTAIL_DSFR_BLOG_ENTRY_MODEL`` setting.
    Defaults to the standard ``wagtail_dsfr.blog.models.BlogEntryPage`` model
    if no custom model is defined.
    """
    model_string = get_blog_entry_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "WAGTAIL_DSFR_BLOG_ENTRY_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"WAGTAIL_DSFR_BLOG_ENTRY_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_events_index_model_string():
    """
    Get the dotted ``app.Model`` name for the events index model as a string.
    """
    return getattr(
        settings,
        "WAGTAIL_DSFR_EVENTS_INDEX_MODEL",
        "wagtail_dsfr_events.EventsIndexPage",
    )


def get_events_index_model():
    """
    Get the events index model from the ``WAGTAIL_DSFR_EVENTS_INDEX_MODEL`` setting.
    Defaults to the standard ``wagtail_dsfr.events.models.EventsIndexPage`` model
    if no custom model is defined.
    """
    model_string = get_events_index_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "WAGTAIL_DSFR_EVENTS_INDEX_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"WAGTAIL_DSFR_EVENTS_INDEX_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_events_entry_model_string():
    """
    Get the dotted ``app.Model`` name for the events entry model as a string.
    """
    return getattr(
        settings,
        "WAGTAIL_DSFR_EVENTS_ENTRY_MODEL",
        "wagtail_dsfr_events.EventEntryPage",
    )


def get_events_entry_model():
    """
    Get the events entry model from the ``WAGTAIL_DSFR_EVENTS_ENTRY_MODEL`` setting.
    Defaults to the standard ``wagtail_dsfr.events.models.EventEntryPage`` model
    if no custom model is defined.
    """
    model_string = get_events_entry_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "WAGTAIL_DSFR_EVENTS_ENTRY_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"WAGTAIL_DSFR_EVENTS_ENTRY_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_content_page_model_string():
    """
    Get the dotted ``app.Model`` name for the content page model as a string.
    """
    return getattr(
        settings,
        "WAGTAIL_DSFR_CONTENT_PAGE_MODEL",
        "wagtail_dsfr_content_manager.ContentPage",
    )


def get_content_page_model():
    """
    Get the content page model from the ``WAGTAIL_DSFR_CONTENT_PAGE_MODEL`` setting.
    Defaults to the standard ``wagtail_dsfr.content_manager.models.ContentPage`` model
    if no custom model is defined.
    """
    model_string = get_content_page_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "WAGTAIL_DSFR_CONTENT_PAGE_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"WAGTAIL_DSFR_CONTENT_PAGE_MODEL refers to model '{model_string}' that has not been installed"
        ) from e
