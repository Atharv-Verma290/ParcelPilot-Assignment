import json
from typing import Any, Dict, Literal, Optional
from langchain.tools import ToolRuntime, tool
from numpy import require
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
def create_ticket(
    account_id: str, 
    subject: str,
    description: str,
    channel: Literal["email", "chat"],
    runtime: ToolRuntime,
    status: Literal["OPEN", "CLOSED"] = "OPEN",
    assigned_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Propose creation of a new ParcelPilot ticket.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role = runtime.state.get("role")
    try:
        require_permission(
            role,
            Permission.WRITE_OPERATIONAL_DATA,
        )
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "create_ticket",
        "proposal": {
            "account_id": account_id,
            "subject": subject,
            "description": description,
            "channel": channel,
            "status": status,
            "assigned_to": assigned_to,
        },
    })

@tool
def update_ticket(
    ticket_id: str,
    runtime: ToolRuntime,
    subject: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[Literal["OPEN", "CLOSED"]] = None,
    assigned_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Propose an update to an existing ParcelPilot ticket.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role = runtime.state.get("role")
    try:
        require_permission(
            role,
            Permission.WRITE_OPERATIONAL_DATA,
        )
    except PermissionError as error:
        return f"Access denied: {error}"

    if all(
        value is None
        for value in (
            subject,
            description,
            status,
            assigned_to,
        )
    ):
        return "At least one field must be provided for update."

    return json.dumps({
        "action": "update_ticket",
        "proposal": {
            "ticket_id": ticket_id,
            "subject": subject,
            "description": description,
            "status": status,
            "assigned_to": assigned_to,
        },
    })


# @tool
# def delete_ticket(
#     ticket_id: str,
#     runtime: ToolRuntime,
# ) -> Dict[str, Any]:
#     """
#     Propose deletion of an existing ParcelPilot ticket.

#     This does NOT modify the database.
#     The proposal must be explicitly approved by a human
#     before execution.
#     """
#     role = runtime.state.get("role")
    
#     try:
#         require_permission(
#             role,
#             Permission.WRITE_OPERATIONAL_DATA,
#         )
#     except PermissionError as error:
#         return f"Access denied: {error}"

#     return json.dumps({
#         "action": "delete_ticket",
#         "proposal": {
#             "ticket_id": ticket_id,
#         },
#     })


@tool
def create_order(
    account_id: str,
    carrier: str,
    shipment_fee_inr: int,
    runtime: ToolRuntime,
    status: Literal["BOOKED", "PICKED_UP", "DELIVERED", "CANCELLED"] = "BOOKED",
    booked_at: Optional[str] = None,
    pickup_window_start: Optional[str] = None,
    pickup_window_end: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Propose creation of a new ParcelPilot order.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """

    role = runtime.state.get("role")

    try:
        require_permission(
            role,
            Permission.WRITE_OPERATIONAL_DATA,
        )
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "create_order",
        "proposal": {
            "account_id": account_id,
            "carrier": carrier,
            "status": status,
            "booked_at": booked_at,
            "pickup_window_start": pickup_window_start,
            "pickup_window_end": pickup_window_end,
            "shipment_fee_inr": shipment_fee_inr,
            "notes": notes,
        },
    })

@tool
def update_order(
    order_id: str,
    runtime: ToolRuntime,
    carrier: Optional[str] = None,
    status: Optional[Literal["BOOKED", "PICKED_UP", "DELIVERED", "CANCELLED"]] = None,
    pickup_window_start: Optional[str] = None,
    pickup_window_end: Optional[str] = None,
    pickup_actual_at: Optional[str] = None,
    shipment_fee_inr: Optional[float] = None,
    carrier_fault: Optional[bool] = None,
    customer_fault: Optional[bool] = None,
    cancellation_requested_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Propose an update to an existing ParcelPilot order.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """

    role = runtime.state.get("role")

    try:
        require_permission(
            role,
            Permission.WRITE_OPERATIONAL_DATA,
        )
    except PermissionError as error:
        return f"Access denied: {error}"

    if all(
        value is None
        for value in (
            carrier,
            status,
            pickup_window_start,
            pickup_window_end,
            pickup_actual_at,
            shipment_fee_inr,
            carrier_fault,
            customer_fault,
            cancellation_requested_at,
            notes,
        )
    ):
        return "At least one field must be provided for update."

    return json.dumps({
        "action": "update_order",
        "proposal": {
            "order_id": order_id,
            "carrier": carrier,
            "status": status,
            "pickup_window_start": pickup_window_start,
            "pickup_window_end": pickup_window_end,
            "pickup_actual_at": pickup_actual_at,
            "shipment_fee_inr": shipment_fee_inr,
            "carrier_fault": carrier_fault,
            "customer_fault": customer_fault,
            "cancellation_requested_at": cancellation_requested_at,
            "notes": notes,
        },
    })

# @tool
# def delete_order(
#     order_id: str,
#     runtime: ToolRuntime,
# ) -> Dict[str, Any]:
#     """
#     Propose deletion of an existing ParcelPilot order.

#     This does NOT modify the database.
#     The proposal must be explicitly approved by a human
#     before execution.
#     """

#     role = runtime.state.get("role")

#     try:
#         require_permission(
#             role,
#             Permission.WRITE_OPERATIONAL_DATA,
#         )
#     except PermissionError as error:
#         return f"Access denied: {error}"

#     return json.dumps({
#         "action": "delete_order",
#         "proposal": {
#             "order_id": order_id,
#         },
#     })


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
        require_permission(role, Permission.MANAGE_FOLLOW_UP_TASKS)
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "create_follow_up_task",
        "proposal": {
            "title": title,
            "description": description,
            "priority": priority,
            "assigned_team": assigned_team,
            "ticket_id": ticket_id,
            "order_id": order_id,
        },
    })


@tool
def update_follow_up_task(
    task_id: int,
    runtime: ToolRuntime,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "URGENT"]] = None,
    assigned_team: Optional[str] = None,
    status: Optional[Literal["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"]] = None,
    ticket_id: Optional[str] = None,
    order_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Propose an update to an existing follow-up task.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role = runtime.state.get("role")

    try:
        require_permission(role, Permission.MANAGE_FOLLOW_UP_TASKS)
    except PermissionError as error:
        return f"Access denied: {error}"

    if all(
        value is None
        for value in (
            title,
            description,
            priority,
            assigned_team,
            status,
            ticket_id,
            order_id,
        )
    ):
        return "At least one field must be provided for update."

    return json.dumps({
        "action": "update_follow_up_task",
        "proposal": {
            "task_id": task_id,
            "title": title,
            "description": description,
            "priority": priority,
            "assigned_team": assigned_team,
            "status": status,
            "ticket_id": ticket_id,
            "order_id": order_id,
        },
    })


# @tool
# def delete_follow_up_task(
#     task_id: int,
#     runtime: ToolRuntime,
# ) -> Dict[str, Any]:
#     """
#     Propose deletion of an existing follow-up task.

#     This does NOT modify the database.
#     The proposal must be explicitly approved by a human
#     before execution.
#     """
#     role = runtime.state.get("role")

#     try:
#         require_permission(role, Permission.MANAGE_FOLLOW_UP_TASKS)
#     except PermissionError as error:
#         return f"Access denied: {error}"

#     return json.dumps({
#         "action": "delete_follow_up_task",
#         "proposal": {
#             "task_id": task_id,
#         },
#     })


@tool 
def create_staff(
    name: str, 
    role: Literal["ADMIN", "OPERATIONS", "SUPPORT"],
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose creation of a new ParcelPilot staff member.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role_value = runtime.state.get("role")

    try:
        require_permission(role_value, Permission.MANAGE_STAFF) 
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "create_staff",
        "proposal": {
            "name": name,
            "role": role,
        }
    })

@tool
def update_staff(
    user_id: str,
    name: Optional[str],
    role: Optional[Literal["SUPPORT", "OPERATIONS", "ADMIN"]],
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose an update to an existing ParcelPilot staff member.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """

    role_value = runtime.state.get("role")

    try:
        require_permission(
            role_value,
            Permission.MANAGE_STAFF,
        )
    except PermissionError as error:
        return f"Access denied: {error}"

    if name is None and role is None:
        return "At least one field must be provided for update."

    return json.dumps({
        "action": "update_staff",
        "proposal": {
            "user_id": user_id,
            "name": name,
            "role": role,
        },
    })


@tool
def delete_staff(
    user_id: str,
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose deletion of an existing ParcelPilot staff member.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role = runtime.state.get("role")


    try:
        require_permission(role, Permission.MANAGE_STAFF)
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "delete_staff",
        "proposal": {
            "user_id": user_id,
        },
    })

all_tools = [
    search_docs_tool,
    query_structured_data,
    create_follow_up_task,
    update_follow_up_task,
    create_staff,
    update_staff,
    delete_staff,
    create_ticket,
    update_ticket,
    create_order,
    update_order,
]