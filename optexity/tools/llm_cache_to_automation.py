import json
from optexity.schema.automation import Automation

SYSTEM_PROMPT = """You convert a list of recorded browser actions into a single
Optexity Automation JSON object. Return ONLY valid JSON matching the provided
JSON schema - no prose, no markdown fences.

When choosing a `command` locator for each step, follow this preference order
(from Optexity's own locator docs): role > label > test_id > text > css > xpath.
Use the step's `resolved_selector_strategy` field to pick the right form:
  role   -> get_by_role("<resolved_selector>", name="<accessible_name>")
  label  -> get_by_label("<resolved_selector>")
  test_id -> get_by_test_id("<resolved_selector>")
  text   -> get_by_text("<resolved_selector>")
  css    -> locator("<resolved_selector>")
  xpath  -> put the value in the node's `xpath` field instead of `command`

Every interaction action MUST include a non-empty `prompt_instructions`."""

def build_messages(url: str, steps: list[dict]) -> list[dict]:
    schema = Automation.model_json_schema()
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({
            "url": url,
            "target_json_schema": schema,
            "cached_steps": steps, # list of CachedStep.model_dump(), post-filter_redundant
        })},
    ]

# Note: In a real environment, litellm.completion would be called here.
# For this scaffold, we stub the completion to avoid API calls without keys.
def llm_build_automation(url: str, steps: list[dict], max_repair_attempts: int = 3) -> Automation:
    messages = build_messages(url, steps)
    raise NotImplementedError("LLM integration requires litellm and API key")
