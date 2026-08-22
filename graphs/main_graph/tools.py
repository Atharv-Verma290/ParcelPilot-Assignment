import json
from typing import Any, Dict, Literal, Optional
from langchain.tools import ToolRuntime, tool
from streamlit.runtime.state.common import user_key_from_element_id 

from .utils import search_docs
from graphs.structured_data.graph import structured_data_graph
from graphs.structured_data.states import StructuredDataState
from auth.authorization import require_permission, Permission

@tool
def search_docs_tool(query: str, runtime: ToolRuntime) -> str:
    """
    Search the Parcel Pilot documentation for information relevant
    to the user's question.

    Use this tool whenever the answer requires information from
    the internal documentation.
    """
    role = runtime.state.get("role")

    try:
        require_permission(role, Permission.READ_DOCUMENTS)
    except PermissionError as error:
        return f"Access denied: {error}"

    results = search_docs(query, k=3)

    if not results:
        return "No relevant documentation was found."

    formatted_results = []

    for i, result in enumerate(results, start=1):
        metadata = result["metadata"]
        source = metadata.get("source", "Unknown")
        section = metadata.get("section")
        page = metadata.get("page")

        location = section or (
            f"Page {page}" if page is not None else "Unknown location"
        )

        formatted_results.append(
            f"""
            Result {i}
            Source: {source}
            Location: {location}

            {result['text']}
            """
        )

        return "\n\n".join(formatted_results)


@tool 
def query_structured_data(instruction: str, runtime: ToolRuntime) -> str:
    """
    Query ParcelPilot's structured operational database.

    Use this tool for questions requiring:
    - account information
    - order information
    - ticket information
    - relationships between accounts, orders, and tickets
    - filtering or aggregating operational records
    - counts, totals, averages, or other calculations
    - time-based analysis of operational data

    Do NOT use this tool for:
    - policies or SOPs
    - customer contract terms
    - product documentation
    - general knowledge

    Provide an explicit instruction describing exactly what
    information you need.

    The tool is read-only and cannot modify the database.
    """
    user_id = runtime.state.get("user_id")
    role = runtime.state.get("role")

    initial_state: StructuredDataState = {
        "instruction": instruction,
        "messages": [],
        "user_id": user_id,
        "role": role,
    }

    result = structured_data_graph.invoke(initial_state)

    messages = result.get("messages", [])

    if not messages:
        return "The strucutured data query returned no response."

    return messages[-1].content


@tool 
def create_follow_up_task(
    title: str, 
    description: str,
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"],
    assigned_team: str,
    runtime: ToolRuntime,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Propose a follow-up task.

    This does NOT create the task in the database.
    The task must be approved by a human before execution.
    """
    role = runtime.state.get("role")

    try:
        require_permission(role, Permission.CREATE_FOLLOW_UP_TASK)
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "title": title,
        "description": description,
        "priority": priority,
        "assigned_team": assigned_team,
        "ticket_id": ticket_id,
        "order_id": order_id,
    })


all_tools = [search_docs_tool, query_structured_data, create_follow_up_task]