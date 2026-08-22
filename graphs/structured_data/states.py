from langgraph.graph import MessagesState


class StructuredDataState(MessagesState):
    instruction: str
    result: str 
    user_id: str 
    role: str
