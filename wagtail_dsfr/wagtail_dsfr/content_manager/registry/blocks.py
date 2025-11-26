"""
Block registry for custom StreamField blocks.

This module provides functionality for registering custom blocks that can be
added to the common StreamField blocks list.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from wagtail import blocks

# Type variable for the block class
BlockType = TypeVar("BlockType", bound=type[blocks.Block])

# Global registry to store registered blocks
_registered_blocks: list[tuple[str, blocks.Block, dict[str, Any]]] = []


def register_common_block(
    name: str | None = None,
    label: str | None = None,
    group: str | None = None,
    **block_kwargs: Any,
) -> Callable[[BlockType], BlockType]:
    """
    Decorator to register a custom block to STREAMFIELD_COMMON_BLOCKS.

    This decorator allows third-party code to add custom blocks to the
    StreamField without modifying the core code.

    Args:
        name: The key name for the block in the StreamField.
              If not provided, uses the snake_case version of the class name.
        label: Human-readable label for the block in the admin interface.
               If not provided, uses the class name with spaces.
        group: Optional group name to organize blocks in the admin interface.
        **block_kwargs: Additional keyword arguments to pass to the block instance.

    Returns:
        The decorator function that registers the block class.

    Example:
        @register_common_block(label="My Custom Block", group="Custom")
        class MyCustomBlock(blocks.StructBlock):
            title = blocks.CharBlock()
            content = blocks.RichTextBlock()

        # Or with a custom name:
        @register_common_block(name="custom", label="Custom Block")
        class MyBlock(blocks.StructBlock):
            pass
    """

    def decorator(block_class: BlockType) -> BlockType:
        # Generate block name from class name if not provided
        block_name = name
        if block_name is None:
            # Convert CamelCase to snake_case
            import re

            block_name = re.sub(r"(?<!^)(?=[A-Z])", "_", block_class.__name__).lower()
            # Remove "block" suffix if present
            if block_name.endswith("_block"):
                block_name = block_name[:-6]

        # Generate label from class name if not provided
        block_label = label
        if block_label is None:
            # Convert CamelCase to space-separated words
            import re

            block_label = re.sub(r"(?<!^)(?=[A-Z])", " ", block_class.__name__)
            # Remove "Block" suffix if present
            if block_label.endswith(" Block"):
                block_label = block_label[:-6]

        # Create block instance with provided kwargs
        block_instance_kwargs = block_kwargs.copy()
        if block_label:
            block_instance_kwargs["label"] = block_label
        if group:
            block_instance_kwargs["group"] = group

        block_instance = block_class(**block_instance_kwargs)

        # Store the registration
        _registered_blocks.append((block_name, block_instance, block_instance_kwargs))

        return block_class

    return decorator


def get_registered_blocks() -> list[tuple[str, blocks.Block]]:
    """
    Get all registered blocks.

    Returns:
        A list of tuples (block_name, block_instance) for all registered blocks.
        This can be appended to STREAMFIELD_COMMON_BLOCKS.
    """
    return [(name, block) for name, block, _ in _registered_blocks]


def clear_registered_blocks() -> None:
    """
    Clear all registered blocks.

    This is mainly useful for testing purposes.
    """
    _registered_blocks.clear()
