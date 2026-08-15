from typing import Literal

from pydantic import BaseModel

SelectorStrategy = Literal['role', 'label', 'test_id', 'text', 'css', 'xpath', 'unknown']


class CachedStep(BaseModel):
	"""One action the agent executed, recorded with enough real locator info to replay it without an LLM."""

	step_index: int
	action_name: str  # the registered browser-use action, e.g. 'click', 'input', 'navigate'
	dom_index: int | None = None  # the transient [n] index, kept for debugging only - never replayed
	resolved_selector: str | None = None
	resolved_selector_strategy: SelectorStrategy = 'unknown'
	accessible_name: str | None = None  # the role's `name=` value, needed to rebuild get_by_role(...)
	value: str | None = None  # text typed / url navigated / option selected
	page_url_before: str
	success: bool
	timestamp: float
