"""
Registry system for custom StreamField blocks.

This module provides a decorator-based system for registering custom blocks
that will be added to STREAMFIELD_COMMON_BLOCKS.

Example usage:
    from wagtail_dsfr.content_manager.registry import register_common_block
    from wagtail import blocks

    @register_common_block(label="My Custom Block", group="Custom")
    class MyBlock(blocks.StructBlock):
        title = blocks.CharBlock()
"""

from .blocks import get_registered_blocks, register_common_block

__all__ = ["register_common_block", "get_registered_blocks"]
