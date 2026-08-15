"""Caching hook for the action-dispatch choke point.

Every action the agent takes funnels through `Registry.execute_action`, where the action name,
its parameters and the target element are all already resolved. Wrapping that one method records
a replayable trace without touching individual action functions or parsing free-text LLM output.

The transient `[n]` DOM index is *not* what gets replayed - it is an artifact of one DOM snapshot
and shifts between runs. What is recorded is the real locator information the index resolved to,
in the order of preference Optexity's own locator docs recommend: role > label > test_id > text >
css > xpath.
"""

import logging
import time
from pathlib import Path

from browser_use.memory_cache.models import CachedStep, SelectorStrategy

logger = logging.getLogger(__name__)

CACHE_PATH = Path('cache.jsonl')

_step_counter = 0
_cache_started = False


def _css_escape(value: str) -> str:
	"""Escape a value for use inside a single-quoted CSS attribute selector."""
	return value.replace('\\', '\\\\').replace("'", "\\'")


def _classify_selector(node) -> tuple[SelectorStrategy, str | None, str | None]:
	"""Map an EnhancedDOMTreeNode to (strategy, selector, accessible_name).

	Only elements with a *distinguishing* accessible name take the role branch. A bare
	`get_by_role('textbox')` matches every text input on the page, which fails Playwright's
	strict mode on replay and silently drops the run back onto the LLM fallback path - the exact
	cost this cache exists to avoid.
	"""
	if not node:
		return 'unknown', None, None

	attributes = node.attributes or {}
	ax_name = (node.ax_node.name or '').strip() if node.ax_node else ''

	if node.ax_node and node.ax_node.role and ax_name:
		return 'role', node.ax_node.role, ax_name

	# get_by_label matches aria-label as well as an associated <label>
	if attributes.get('aria-label'):
		return 'label', attributes['aria-label'], None

	for attr in ('data-testid', 'data-test-id'):
		if attributes.get(attr):
			return 'test_id', attributes[attr], None

	if ax_name:
		return 'text', ax_name, None

	if attributes.get('id'):
		return 'css', f'#{attributes["id"]}', None

	# The `name` attribute is not a label - it only works as an attribute selector.
	if node.node_name.lower() in ('input', 'textarea', 'select') and attributes.get('name'):
		return 'css', f'{node.node_name.lower()}[name=\'{_css_escape(attributes["name"])}\']', None

	if attributes.get('placeholder'):
		return 'css', f'[placeholder=\'{_css_escape(attributes["placeholder"])}\']', None

	try:
		if node.xpath:
			return 'xpath', node.xpath, None
	except Exception:
		pass

	return 'unknown', None, None


def _write_step(step: CachedStep) -> None:
	"""Append one step, truncating the file on the first write of this process.

	Each agentic run is a fresh worker process, so truncating here keeps `cache.jsonl` scoped to
	exactly one run - otherwise the converter reads a cache mixed across runs.
	"""
	global _cache_started

	mode = 'a' if _cache_started else 'w'
	with CACHE_PATH.open(mode) as f:
		f.write(step.model_dump_json() + '\n')
	_cache_started = True


def cached_execute_action(original_execute_action):
	"""Wrap `Registry.execute_action` so every dispatched action is recorded to `cache.jsonl`."""

	async def wrapper(self, action_name: str, params: dict, *args, **kwargs):
		global _step_counter

		browser_session = kwargs.get('browser_session') or (args[0] if args else None)
		page_url_before = ''
		node = None
		dom_index = params.get('index') if isinstance(params, dict) else None

		if browser_session is not None:
			try:
				page_url_before = await browser_session.get_current_page_url()
				if dom_index is not None:
					node = await browser_session.get_element_by_index(dom_index)
			except Exception as e:
				logger.debug(f'Could not capture pre-action state for {action_name}: {e}')

		result = await original_execute_action(self, action_name, params, *args, **kwargs)

		strategy, selector, accessible_name = _classify_selector(node)

		value = None
		if isinstance(params, dict):
			value = params.get('text') or params.get('url') or params.get('query') or params.get('value')

		success = True
		if getattr(result, 'error', None):
			success = False
		elif getattr(result, 'success', None) is False:
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

		try:
			_write_step(step)
			logger.debug(f'Cached step {step.step_index} ({action_name}) as {strategy}={selector!r}')
		except Exception as e:
			# A caching failure must never take down the agent run it is observing.
			logger.warning(f'Failed to write step {step.step_index} to {CACHE_PATH}: {e}')

		return result

	return wrapper
