from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .nodes import (
    agent_node,
    human_node,
    perform_action,
    process_tool_result,
    route_human,
)
from .states import AgentState
from .tools import all_tools


def build_graph():
    """
    Compile the main support-agent graph with an in-memory checkpointer.

    The loop is agent → tools (optional) → process_tool_result → agent,
    with a human interrupt after the agent when no tools are called.
    Approved pending actions go through `perform_action`.

    Returns:
        A compiled LangGraph runnable.
    """
    builder = StateGraph(AgentState)
    builder.add_node("human", human_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(all_tools))
    builder.add_node("process_tool_result", process_tool_result)
    builder.add_node("perform_action", perform_action)
    builder.set_entry_point("agent")

    builder.add_conditional_edges(
        "agent",
        tools_condition,
        {"tools": "tools", "__end__": "human"},
    )
    builder.add_conditional_edges(
        "human",
        route_human,
        {
            "perform_action": "perform_action",
            "agent": "agent",
            "__end__": END,
        },
    )
    builder.add_edge("tools", "process_tool_result")
    builder.add_edge("process_tool_result", "agent")
    builder.add_edge("perform_action", "agent")

    return builder.compile(checkpointer=InMemorySaver())
