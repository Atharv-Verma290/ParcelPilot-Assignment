from typing import Any, Dict, Literal, Optional
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class ActionProposalState(MessagesState):
    instruction: str

    # Populated once the proposal agent determines the action.
    action: Optional[str] = None

    # Structured parameters for the proposed action.
    proposal: Dict[str, Any] 

    # Context inherited from the main agent.
    user_id: str
    role: str

    # Used when proposal generation fails.
    error: Optional[str] = None


class ActionProposal(BaseModel):
    action: Literal[
        "create_follow_up_task",
        "update_follow_up_task",
        "delete_follow_up_task",
        "create_staff",
        "update_staff",
        "delete_staff",
        "create_ticket",
        "update_ticket",
        "create_order",
        "update_order",
    ] = Field(
        description="The action to be performed."
    )

    proposal: dict[str, Any] = Field(
        description=(
            "Parameters for the selected action. The parameters must "
            "correspond to the selected action and contain only the "
            "fields required or explicitly requested for that action."
        )
    )