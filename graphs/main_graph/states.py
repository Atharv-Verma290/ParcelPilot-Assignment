from typing import Any, Dict
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    pending_action: Dict[str, Any] 