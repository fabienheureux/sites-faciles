# Swappable Models Implementation

## Overview

This document describes the implementation of a swappable model system for wagtail_dsfr, inspired by Django's `AUTH_USER_MODEL` and Wagtail's `WAGTAILIMAGES_IMAGE_MODEL` patterns.

## Problem Statement

Users need a way to customize StreamField blocks in wagtail_dsfr pages without:
- Generating migrations in the package itself
- Causing migration conflicts between users
- Modifying the core package code

Additionally:
- `PageChooserBlock` in the package hardcoded references to concrete models like `"wagtail_dsfr_blog.BlogIndexPage"`
- Users need flexibility to extend models with custom fields and blocks

## Solution: Swappable Models Pattern

We implemented a two-part solution following Django/Wagtail best practices:

### 1. Swappable Model References (Django/Wagtail Pattern)

Created helper functions to get models from settings:

```python
# wagtail_dsfr/utils/models.py
def get_blog_index_model_string():
    return getattr(
        settings,
        "WAGTAIL_DSFR_BLOG_INDEX_MODEL",
        "wagtail_dsfr_blog.BlogIndexPage",
    )

def get_blog_index_model():
    model_string = get_blog_index_model_string()
    return apps.get_model(model_string, require_ready=False)
```

Similar functions for:
- `get_blog_entry_model()`
- `get_events_index_model()`
- `get_events_entry_model()`
- `get_content_page_model()`

### 2. Custom ChooserBlock Classes

Created custom `PageChooserBlock` subclasses that use swappable models:

```python
# wagtail_dsfr/content_manager/blocks/choosers.py
class BlogIndexChooserBlock(PageChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail_dsfr.utils.models import get_blog_index_model
        return get_blog_index_model()

class EventsIndexChooserBlock(PageChooserBlock):
    @cached_property
    def target_model(self):
        from wagtail_dsfr.utils.models import get_events_index_model
        return get_events_index_model()
```

### 2. Updated Block Definitions

Modified blocks to use the new chooser blocks:

```python
# wagtail_dsfr/content_manager/blocks/related_entries.py
from wagtail_dsfr.content_manager.blocks.choosers import (
    BlogIndexChooserBlock,
    EventsIndexChooserBlock,
)

class BlogRecentEntriesBlock(blocks.StructBlock):
    blog = BlogIndexChooserBlock(label=_("Blog"))  # Instead of PageChooserBlock with page_type
```

## Usage

### Default Behavior (No Configuration Required)

By default, the package uses concrete models:
- `wagtail_dsfr_blog.BlogIndexPage`
- `wagtail_dsfr_blog.BlogEntryPage`
- `wagtail_dsfr_events.EventsIndexPage`
- `wagtail_dsfr_events.EventEntryPage`
- `wagtail_dsfr_content_manager.ContentPage`

Users can use the package without any special configuration.

### Advanced: Custom Models

For users who need complete control (e.g., to customize StreamField blocks), they can create their own models and configure them:

```python
# settings.py
WAGTAIL_DSFR_BLOG_INDEX_MODEL = 'myapp.CustomBlogIndexPage'
WAGTAIL_DSFR_BLOG_ENTRY_MODEL = 'myapp.CustomBlogEntryPage'
WAGTAIL_DSFR_EVENTS_INDEX_MODEL = 'myapp.CustomEventsIndexPage'
WAGTAIL_DSFR_EVENTS_ENTRY_MODEL = 'myapp.CustomEventEntryPage'
WAGTAIL_DSFR_CONTENT_PAGE_MODEL = 'myapp.CustomContentPage'
```

The package's `PageChooserBlock` instances will automatically use the configured models.

## paquet_facile.py Updates

The build script now handles the `{package_name_upper}` placeholder:

```python
def expand_rules(config: dict[str, Any]) -> list[dict[str, Any]]:
    package_name: str = config.get("package_name", "sites_faciles")
    package_name_upper: str = package_name.upper()
    
    # Replace placeholders
    search = search.replace("{package_name}", package_name)
    search = search.replace("{package_name_upper}", package_name_upper)
```

This allows replacement rules like:

```yaml
- search: 'WAGTAIL_DSFR_BLOG_INDEX_MODEL'
  replace: '{package_name_upper}_BLOG_INDEX_MODEL'
```

## Benefits

1. **No Migration Conflicts**: Custom blocks don't modify package models
2. **Flexibility**: Users can create completely custom models if needed
3. **Backward Compatible**: Default behavior uses concrete models (no breaking changes)
4. **Follows Best Practices**: Uses established Django/Wagtail patterns
5. **Dynamic References**: PageChooserBlock automatically uses configured models

## Documentation

The README template has been updated with:
1. Instructions for using swappable models
2. Examples of custom model configuration
3. Reference to helper functions
4. Examples of custom ChooserBlock usage

## Demo Implementation

A complete working example is available in the `demo/` directory:

- **`demo/custom_blog/`**: Complete Django app demonstrating swappable models
  - Custom blog models extending base models
  - Custom StreamField blocks (HighlightBox, ImageText, CodeBlock)
  - Block templates with built-in styling
  - Comprehensive documentation

See `demo/SWAPPABLE_MODELS_DEMO.md` and `demo/custom_blog/README.md` for details.

## Files Changed

1. **New Files**:
   - `wagtail_dsfr/wagtail_dsfr/utils/models.py` - Model getter functions
   - `wagtail_dsfr/wagtail_dsfr/utils/__init__.py` - Utils package init
   - `wagtail_dsfr/wagtail_dsfr/content_manager/blocks/choosers.py` - Custom chooser blocks
   - `templates/utils/models.template.py` - Template for utils/models.py
   - `templates/content_manager/blocks/choosers.template.py` - Template for choosers
   - `demo/custom_blog/` - Complete demo implementation

2. **Modified Files**:
   - `wagtail_dsfr/wagtail_dsfr/content_manager/blocks/related_entries.py` - Use new choosers
   - `templates/README.template.md` - Updated documentation (removed registry, added swappable models docs)
   - `search-and-replace.yml` - Added swappable model replacement rules
   - `paquet_facile.py` - Handle `{package_name_upper}` placeholder, process utils templates
   - `demo/demo/settings/base.py` - Added swappable model configuration example

3. **Removed Files**:
   - `wagtail_dsfr/wagtail_dsfr/content_manager/registry/` - Removed non-functional registry system
   - `templates/content_manager/registry/` - Removed registry templates

## Future Improvements

Potential enhancements:
1. Create abstract base models for users who want to subclass
2. Add more swappable models (e.g., for Category, Person, Organization)
3. Add tests for swappable model functionality
4. Create more demo examples (events, content pages)
