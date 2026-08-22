from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .nodes import structured_data_agent
from .states import StructuredDataState
from .tools import execute_sql

builder = StateGraph(StructuredDataState)

builder.add_node("structured_data_agent", structured_data_agent)
builder.add_node("tools", ToolNode([execute_sql]))
builder.set_entry_point("structured_data_agent")

builder.add_conditional_edges("structured_data_agent", tools_condition, {"tools": "tools", "__end__": END})
builder.add_edge("tools", "structured_data_agent")

structured_data_graph = builder.compile()