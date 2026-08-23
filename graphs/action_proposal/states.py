from typing import Any, Dict, Literal
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class ActionProposalState(MessagesState):
    instruction: str 
    action: str 
    proposal: Dict[str, Any]
    user_id: str
    role: str 
    error: str


class ActionProposal(BaseModel):
    action: Literal[
        "create_follow_up_task",
        "create_staff",
        "update_staff",
        "delete_staff",
    ]

    proposal: dict[str, Any] = Field(
        description="Parameters required to execute the proposed action."
    )