from typing import Literal 

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition 

from .states import ActionProposalState
from .nodes import create_proposal, structure_proposal
from .tools import proposal_tools 

tools_node = ToolNode(proposal_tools) 


builder = StateGraph(ActionProposalState) 
builder.add_node("tools", tools_node) 
builder.add_node("create_proposal", create_proposal)
builder.add_node("structure_proposal", structure_proposal)

builder.set_entry_point("create_proposal")

builder.add_conditional_edges("create_proposal", tools_condition, {"tools": "tools", "__end__": "structure_proposal"})
builder.add_edge("tools", "structure_proposal")
builder.add_edge("structure_proposal", END)

action_proposal_graph = builder.compile()