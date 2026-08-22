from langgraph.graph import MessagesState


class StructuredDataState(MessagesState):
    instruction: str
    result: str
