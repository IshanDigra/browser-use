from pydantic import BaseModel
from typing import Literal

class CachedStep(BaseModel):
    step_index: int
    action_name: str                  # e.g. "click_element", "input_text"
    dom_index: int | None = None      # the transient [n] index, kept for debugging only
    resolved_selector: str | None = None
    resolved_selector_strategy: Literal[
        "role", "label", "test_id", "text", "css", "xpath", "unknown"
    ] = "unknown"
    accessible_name: str | None = None  # e.g. role's `name=` value, needed to rebuild get_by_role(...)
    value: str | None = None            # text typed / url navigated / option selected
    page_url_before: str
    success: bool
    timestamp: float
