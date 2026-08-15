from optexity.schema.automation import Automation

def _build_command(step) -> tuple[str | None, str | None]:
    """Returns (command, xpath) per Optexity's locator preference order."""
    if step.resolved_selector_strategy == "role":
        name = step.accessible_name or ""
        return f'get_by_role("{step.resolved_selector}", name="{name}")', None
    if step.resolved_selector_strategy == "label":
        return f'get_by_label("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "test_id":
        return f'get_by_test_id("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "text":
        return f'get_by_text("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "css":
        return f'locator("{step.resolved_selector}")', None
    if step.resolved_selector_strategy == "xpath":
        return None, step.resolved_selector
    return None, None # unknown - will rely on prompt_instructions only

_ACTION_MAP = {
    "click_element_by_index": "click_element",
    "click": "click_element",
    "input_text": "input_text",
    "input": "input_text",
    "go_to_url": "go_to_url",
    "select_dropdown_option": "select_option",
}

def build_node(step) -> dict:
    optexity_action = _ACTION_MAP.get(step.action_name)
    if optexity_action is None:
        raise ValueError(f"No mapping for browser-use action '{step.action_name}' - "
                         f"extend _ACTION_MAP or handle it explicitly")

    command, xpath = _build_command(step)
    body = {
        "command": command,
        "xpath": xpath,
        "prompt_instructions": f"Perform {optexity_action} for step {step.step_index} "
                               f"(derived from a cached agentic run)",
    }
    if optexity_action == "input_text":
        body["input_text"] = step.value
    elif optexity_action == "select_option":
        body["option_text"] = step.value

    return {
        "type": "action_node",
        "interaction_action": {optexity_action: body},
    }

def build_automation(url: str, steps: list) -> Automation:
    automation_dict = {
        "url": url,
        "parameters": {"input_parameters": {}, "generated_parameters": {}},
        "nodes": [build_node(s) for s in steps],
    }
    # Validate against the real schema before anything is written to disk -
    # catches drift immediately instead of shipping a malformed automation.
    return Automation.model_validate(automation_dict)

if __name__ == "__main__":
    from filter import load_steps, filter_redundant # Phase 3, same fork
    import sys

    try:
        steps = filter_redundant(load_steps("cache.jsonl"))
        if not steps:
             print("No steps to convert")
             sys.exit(0)

        url = steps[0].page_url_before or "https://www.roboform.com/filling-test-all-fields"

        automation = build_automation(url, steps)

        with open("test_automation_cached.json", "w") as f:
            f.write(automation.model_dump_json(indent=2))
        print("Generated test_automation_cached.json successfully")
    except FileNotFoundError:
        print("cache.jsonl not found")
