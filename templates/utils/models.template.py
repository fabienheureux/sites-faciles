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
        "{package_name_upper}_BLOG_INDEX_MODEL",
        "{package_name}_blog.BlogIndexPage",
    )


def get_blog_index_model():
    """
    Get the blog index model from the ``{package_name_upper}_BLOG_INDEX_MODEL`` setting.
    Defaults to the standard ``{package_name}.blog.models.BlogIndexPage`` model
    if no custom model is defined.
    """
    model_string = get_blog_index_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "{package_name_upper}_BLOG_INDEX_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{package_name_upper}_BLOG_INDEX_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_blog_entry_model_string():
    """
    Get the dotted ``app.Model`` name for the blog entry model as a string.
    """
    return getattr(
        settings,
        "{package_name_upper}_BLOG_ENTRY_MODEL",
        "{package_name}_blog.BlogEntryPage",
    )


def get_blog_entry_model():
    """
    Get the blog entry model from the ``{package_name_upper}_BLOG_ENTRY_MODEL`` setting.
    Defaults to the standard ``{package_name}.blog.models.BlogEntryPage`` model
    if no custom model is defined.
    """
    model_string = get_blog_entry_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "{package_name_upper}_BLOG_ENTRY_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{package_name_upper}_BLOG_ENTRY_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_events_index_model_string():
    """
    Get the dotted ``app.Model`` name for the events index model as a string.
    """
    return getattr(
        settings,
        "{package_name_upper}_EVENTS_INDEX_MODEL",
        "{package_name}_events.EventsIndexPage",
    )


def get_events_index_model():
    """
    Get the events index model from the ``{package_name_upper}_EVENTS_INDEX_MODEL`` setting.
    Defaults to the standard ``{package_name}.events.models.EventsIndexPage`` model
    if no custom model is defined.
    """
    model_string = get_events_index_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "{package_name_upper}_EVENTS_INDEX_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{package_name_upper}_EVENTS_INDEX_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_events_entry_model_string():
    """
    Get the dotted ``app.Model`` name for the events entry model as a string.
    """
    return getattr(
        settings,
        "{package_name_upper}_EVENTS_ENTRY_MODEL",
        "{package_name}_events.EventEntryPage",
    )


def get_events_entry_model():
    """
    Get the events entry model from the ``{package_name_upper}_EVENTS_ENTRY_MODEL`` setting.
    Defaults to the standard ``{package_name}.events.models.EventEntryPage`` model
    if no custom model is defined.
    """
    model_string = get_events_entry_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "{package_name_upper}_EVENTS_ENTRY_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{package_name_upper}_EVENTS_ENTRY_MODEL refers to model '{model_string}' that has not been installed"
        ) from e


def get_content_page_model_string():
    """
    Get the dotted ``app.Model`` name for the content page model as a string.
    """
    return getattr(
        settings,
        "{package_name_upper}_CONTENT_PAGE_MODEL",
        "{package_name}_content_manager.ContentPage",
    )


def get_content_page_model():
    """
    Get the content page model from the ``{package_name_upper}_CONTENT_PAGE_MODEL`` setting.
    Defaults to the standard ``{package_name}.content_manager.models.ContentPage`` model
    if no custom model is defined.
    """
    model_string = get_content_page_model_string()
    try:
        return apps.get_model(model_string, require_ready=False)
    except ValueError as e:
        raise ImproperlyConfigured(
            "{package_name_upper}_CONTENT_PAGE_MODEL must be of the form 'app_label.model_name'"
        ) from e
    except LookupError as e:
        raise ImproperlyConfigured(
            f"{package_name_upper}_CONTENT_PAGE_MODEL refers to model '{model_string}' that has not been installed"
        ) from e
