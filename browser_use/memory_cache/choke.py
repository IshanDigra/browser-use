import time
from pathlib import Path
from typing import Any
import inspect
from loguru import logger
from .models import CachedStep
import json
import asyncio

CACHE_PATH = Path("cache.jsonl")
_step_counter = 0

def _classify_selector(node) -> tuple[str, str | None, str | None]:
    """Extract selector info from an EnhancedDOMTreeNode"""
    if not node:
        return "unknown", None, None

    # Try role/name
    if node.ax_node and node.ax_node.role:
        return "role", node.ax_node.role, node.ax_node.name

    # Try label (for inputs usually indicated by name or aria-label)
    if 'aria-label' in node.attributes:
        return "label", node.attributes['aria-label'], None

    if node.node_name.lower() in ('input', 'textarea', 'select') and 'name' in node.attributes:
        return "label", node.attributes['name'], None

    # Try test_id
    for attr in ['data-testid', 'data-test-id']:
        if attr in node.attributes:
            return "test_id", node.attributes[attr], None

    # Try text
    if node.ax_node and node.ax_node.name and node.ax_node.name.strip():
        return "text", node.ax_node.name.strip(), None

    # Try CSS class/id
    if 'id' in node.attributes:
        return "css", f"#{node.attributes['id']}", None

    if 'class' in node.attributes:
        # Just use first class if multiple
        classes = node.attributes['class'].split()
        if classes:
             return "css", f".{classes[0]}", None

    # Fallback to xpath
    try:
        return "xpath", node.xpath, None
    except Exception:
        pass

    return "unknown", None, None

def cached_execute_action(original_execute_action):
    """Decorator to cache executed actions."""
    async def wrapper(self, action_name: str, params: dict, *args, **kwargs):
        global _step_counter

        # Get browser session to extract info BEFORE action
        browser_session = kwargs.get('browser_session') or (args[0] if args else None)
        page_url_before = ""
        node = None
        dom_index = params.get('index')

        if browser_session:
            try:
                page_url_before = await browser_session.get_current_page_url()
                if dom_index is not None:
                     node = await browser_session.get_element_by_index(dom_index)
            except Exception as e:
                 logger.debug(f"Failed to get info before action: {e}")

        # Execute actual action
        result = await original_execute_action(self, action_name, params, *args, **kwargs)

        # Extract selector info
        strategy, selector, accessible_name = _classify_selector(node)

        # Try to infer typed text / value
        value = params.get('text') or params.get('url') or params.get('value')
        if not value and action_name == 'select_dropdown_option':
             value = params.get('text')

        success = True
        if hasattr(result, 'error') and result.error:
             success = False
        elif hasattr(result, 'success') and result.success is False:
             success = False

        step = CachedStep(
            step_index=_step_counter,
            action_name=action_name,
            dom_index=dom_index,
            resolved_selector=selector,
            resolved_selector_strategy=strategy,
            accessible_name=accessible_name,
            value=value,
            page_url_before=page_url_before,
            success=success,
            timestamp=time.time(),
        )

        _step_counter += 1

        # Append to cache
        try:
            with CACHE_PATH.open("a") as f:
                f.write(step.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to write to cache: {e}")

        return result

    return wrapper
