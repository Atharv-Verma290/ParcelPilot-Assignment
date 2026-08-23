import json

from langchain.tools import ToolRuntime, tool

from .utils import search_docs
from graphs.structured_data.graph import structured_data_graph
from graphs.structured_data.states import StructuredDataState
from graphs.action_proposal.graph import action_proposal_graph
from graphs.action_proposal.states import ActionProposalState
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
def propose_action(instruction: str, runtime: ToolRuntime) -> str:
    """
    Create a structured proposal for an operational action.

    Provide a detailed instruction describing the action that should
    be proposed and all relevant information available from the user
    or previous investigation.

    The action proposal workflow determines the appropriate supported
    action, gathers any required information, and returns a normalized
    action proposal.

    This tool does not execute the action or modify the database.
    """
    user_id = runtime.state.get("user_id")
    role = runtime.state.get("role")

    initial_state: ActionProposalState = {
        "instruction": instruction,
        "messages": [],
        "user_id": user_id,
        "role": role,
    }

    result = action_proposal_graph.invoke(initial_state)

    if result.get("error"):
        return f"Action proposal failed: {result['error']}"

    action = result.get("action")
    proposal = result.get("proposal") 

    if not action or not proposal:
        return "The action proposal workflow returned an invalid result."

    return json.dumps({
        "action": action,
        "proposal": proposal,
    })

all_tools = [
    search_docs_tool,
    query_structured_data,
    propose_action,
]
