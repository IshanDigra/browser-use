from models import CachedStep

def load_steps(path: str) -> list[CachedStep]:
    with open(path) as f:
        return [CachedStep.model_validate_json(line) for line in f if line.strip()]

def filter_redundant(steps: list[CachedStep]) -> list[CachedStep]:
    kept: list[CachedStep] = []
    last_index_by_selector: dict[str, int] = {}

    for step in steps:
        if not step.success:
            continue # drop failed attempts; only the eventual success matters

        key = step.resolved_selector or f"idx:{step.dom_index}"

        # last-write-wins: if the same field/element was acted on again
        # before this run ends, the later value is the real one - drop
        # the earlier attempt rather than keeping both.
        if key in last_index_by_selector and step.action_name in ("input_text", "input", "select_option", "select_dropdown_option"):
            kept[last_index_by_selector[key]] = step
            continue

        last_index_by_selector[key] = len(kept)
        kept.append(step)

    return kept
