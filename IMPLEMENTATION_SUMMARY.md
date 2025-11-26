# Implementation Summary: Swappable Models & Demo

## Overview

This implementation removes the non-functional `@register_common_block` decorator system and replaces it with a working **swappable models pattern** (similar to Django's `AUTH_USER_MODEL` and Wagtail's `WAGTAILIMAGES_IMAGE_MODEL`).

A complete working demo has been added to showcase this new approach.

## What Was Removed

### 1. Registry System (Non-Functional)
The `@register_common_block` decorator system was removed because:
- ❌ It loaded blocks at runtime but models are defined at import time
- ❌ Custom blocks couldn't actually be used in existing pages
- ❌ No way to add blocks without causing migration conflicts
- ❌ Misleading documentation suggesting it worked

**Files Removed:**
- `wagtail_dsfr/wagtail_dsfr/content_manager/registry/__init__.py`
- `wagtail_dsfr/wagtail_dsfr/content_manager/registry/blocks.py`
- `templates/content_manager/registry/__init__.template.py`
- `templates/content_manager/registry/blocks.template.py`

**Files Modified to Remove Registry:**
- `wagtail_dsfr/wagtail_dsfr/content_manager/apps.py` - Removed `ready()` method
- `templates/content_manager/apps.template.py` - Removed `ready()` method
- `templates/README.template.md` - Removed all registry documentation (~100 lines)
- `paquet_facile.py` - Removed registry template processing code

## What Was Added

### 1. Swappable Models Infrastructure

**New Helper Functions** (`wagtail_dsfr/utils/models.py`):
```python
get_blog_index_model()
get_blog_entry_model()
get_events_index_model()
get_events_entry_model()
get_content_page_model()
```

These functions read Django settings to determine which models to use, with sensible defaults.

**New Custom ChooserBlocks** (`wagtail_dsfr/content_manager/blocks/choosers.py`):
```python
BlogIndexChooserBlock
EventsIndexChooserBlock
```

These automatically use the configured models instead of hardcoded references.

**Template Files:**
- `templates/utils/models.template.py` - Template for helper functions
- `templates/utils/__init__.template.py` - Utils package init
- `templates/content_manager/blocks/choosers.template.py` - Template for chooser blocks

**Updated `paquet_facile.py`:**
- Processes `{package_name_upper}` placeholder for settings constants
- Processes utils templates
- Removed registry processing code

### 2. Complete Demo Implementation

Created `demo/custom_blog/` - a full Django app demonstrating the pattern:

**Structure:**
```
demo/custom_blog/
├── __init__.py
├── apps.py                      # App configuration
├── models.py                    # Custom blog models
├── blocks.py                    # Custom StreamField blocks
├── admin.py                     # Admin config
├── tests.py                     # Tests placeholder
├── README.md                    # Detailed documentation
├── migrations/
│   └── __init__.py
└── templates/
    └── custom_blog/
        └── blocks/
            ├── highlight_box.html
            ├── image_text.html
            └── code.html
```

**Custom Models:**
- `CustomBlogIndexPage` - Extends `BlogIndexPage` with `featured_text` field
- `CustomBlogEntryPage` - Extends `BlogEntryPage` with `reading_time` and `difficulty` fields

**Custom Blocks:**
- `HighlightBoxBlock` - Colored highlight box with title and content
- `ImageTextBlock` - Image with text side-by-side layout
- `CodeBlock` - Code block with syntax highlighting

**Block Templates:**
- Self-contained HTML with inline CSS
- Responsive layouts
- DSFR-compatible styling

### 3. Documentation

**New Documentation Files:**
- `SWAPPABLE_MODELS_IMPLEMENTATION.md` - Technical implementation details
- `demo/SWAPPABLE_MODELS_DEMO.md` - Demo overview and quick start
- `demo/custom_blog/README.md` - Complete usage guide with examples

**Updated Documentation:**
- `templates/README.template.md` - Removed registry docs, added swappable models section
- Clear explanation of the pattern
- Step-by-step configuration guide
- Examples of custom models and blocks

### 4. Demo Configuration

**Updated `demo/demo/settings/base.py`:**
```python
INSTALLED_APPS = [
    "demo.apps.DemoConfig",
    "home",
    "search",
    "custom_blog",  # Added before wagtail_dsfr apps
    # ... rest of apps
]

# Swappable models configuration
WAGTAIL_DSFR_BLOG_INDEX_MODEL = "custom_blog.CustomBlogIndexPage"
WAGTAIL_DSFR_BLOG_ENTRY_MODEL = "custom_blog.CustomBlogEntryPage"
```

## How It Works

### The Problem with the Old Approach

```python
# ❌ Doesn't work - blocks added at runtime
@register_common_block(label="My Block")
class MyBlock(blocks.StructBlock):
    pass

# Model is already defined - can't use the new block!
class BlogEntryPage(Page):
    body = StreamField(STREAMFIELD_COMMON_BLOCKS, ...)
```

### The Solution: Swappable Models

```python
# ✅ Works - complete control over blocks
class CustomBlogEntryPage(BaseBlogEntryPage):
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS + [
            ("my_block", MyBlock()),  # Add any blocks you want!
        ],
        # ...
    )

# Configure in settings.py
WAGTAIL_DSFR_BLOG_ENTRY_MODEL = "myapp.CustomBlogEntryPage"
```

## Benefits

✅ **Actually Works**: Custom blocks are truly available in your pages

✅ **Clean Migrations**: Your migrations stay in your app, not in the package

✅ **Maintainable**: Clear, explicit configuration

✅ **Flexible**: Add fields, blocks, methods - complete control

✅ **Upgradeable**: Package updates won't conflict with your customizations

✅ **Well-Documented**: Complete examples and clear guides

✅ **Best Practices**: Follows Django and Wagtail patterns

## Usage Example

### For Package Users

1. Create your custom models in your Django app
2. Configure settings to use your models
3. Run migrations
4. Create pages with your custom blocks!

See `demo/custom_blog/README.md` for the complete step-by-step guide.

### For Package Maintainers

When building packages from this template:
- Helper functions in `utils/models.py` are automatically generated
- Chooser blocks are automatically generated
- Settings constants use `{package_name_upper}` prefix
- Everything works out of the box

## Testing the Demo

```bash
cd demo

# Make migrations for custom_blog
python manage.py makemigrations custom_blog

# Apply migrations
python manage.py migrate

# Run the server
python manage.py runserver

# Create blog pages in the Wagtail admin to see custom blocks!
```

## Files Summary

**Removed:** 4 files (registry system)
**Added:** 15+ files (swappable models + demo)
**Modified:** 8 files (remove registry, add swappable models)

## Next Steps

1. ✅ Remove registry system - DONE
2. ✅ Implement swappable models - DONE
3. ✅ Create demo - DONE
4. ✅ Update documentation - DONE
5. 🔄 Test with real users
6. 🔄 Add more swappable models (events, content pages)
7. 🔄 Create abstract base models
8. 🔄 Add automated tests

## Migration Notes

For existing users who might have tried to use the registry system:
- The `@register_common_block` decorator is no longer available
- Use swappable models instead (see documentation)
- No breaking changes for users who weren't using the registry

## Questions?

See the documentation:
- `SWAPPABLE_MODELS_IMPLEMENTATION.md` - Technical details
- `demo/SWAPPABLE_MODELS_DEMO.md` - Demo overview
- `demo/custom_blog/README.md` - Step-by-step guide
- `templates/README.template.md` - User-facing docs
