from pydantic import BaseModel, Field

class InteractionAction(BaseModel):
    click_element: dict | None = None
    input_text: dict | None = None
    select_option: dict | None = None
    check: dict | None = None
    go_to_url: dict | None = None
    agentic_task: dict | None = None

class ActionNode(BaseModel):
    type: str = "action_node"
    interaction_action: InteractionAction

class Automation(BaseModel):
    url: str
    parameters: dict = Field(default_factory=lambda: {"input_parameters": {}, "generated_parameters": {}})
    nodes: list[ActionNode] = Field(default_factory=list)
