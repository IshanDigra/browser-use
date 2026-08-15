from optexity.schema.automation import Automation
from filter import load_steps, filter_redundant
from cache_to_automation import build_node

MAX_HEALING_ITERATIONS = 3

def run_single_node(automation: Automation, node_index: int) -> bool:
    """Executes exactly one node of an automation and returns whether it
    succeeded. Placeholder - wire this to whatever the local dev harness
    (Phase 0/1) exposes for running a subset of nodes; the goal doc's
    child_process.py override is the natural place to add single-node
    execution if it isn't already exposed."""
    raise NotImplementedError("Requires Optexity inference runner")

def run_with_self_healing(
    automation: Automation,
    remaining_goal_by_node: dict[int, str],
) -> Automation:
    """`remaining_goal_by_node` maps a node index to a natural-language
    description of what that node was meant to accomplish - used to build
    the scoped agentic_task fallback when that node fails."""

    for iteration in range(MAX_HEALING_ITERATIONS):
        failure_index = next(
            (i for i, _ in enumerate(automation.nodes) if not run_single_node(automation, i)),
            None,
        )

        if failure_index is None:
            return automation # every node succeeded

        goal = remaining_goal_by_node.get(
            failure_index, "Recover and complete the remaining workflow"
        )
        recovery_automation = Automation.model_validate({
            "url": automation.url,
            "parameters": {"input_parameters": {}, "generated_parameters": {}},
            "nodes": [{
                "type": "action_node",
                "interaction_action": {
                    "agentic_task": {"task": goal, "max_steps": 10, "backend": "browser_use"},
                },
            }],
        })
        run_single_node(recovery_automation, 0) # Phase 2's hook is already active for agentic_task

        new_steps = filter_redundant(load_steps("cache.jsonl"))
        if new_steps:
            automation.nodes[failure_index] = build_node(new_steps[-1])

    raise RuntimeError(
        f"Automation still failing at a node after {MAX_HEALING_ITERATIONS} healing attempts - "
        f"needs a human look, not another automated retry."
    )
