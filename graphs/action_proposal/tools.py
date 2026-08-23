import json
from typing import Any, Dict, Literal, Optional
from langchain.tools import ToolRuntime, tool

from auth.authorization import Permission, require_permission


@tool
def create_ticket(
    account_id: str,
    subject: str,
    description: str,
    channel: Literal["email", "chat"],
    runtime: ToolRuntime,
    status: Literal["open", "closed"] = "open",
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
    status: Optional[Literal["open", "closed"]] = None,
    assigned_to: Optional[str] = None,
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


@tool
def delete_ticket(
    ticket_id: str,
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose deletion of an existing ParcelPilot ticket.

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
        "action": "delete_ticket",
        "proposal": {
            "ticket_id": ticket_id,
        },
    })


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


@tool
def delete_order(
    order_id: str,
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose deletion of an existing ParcelPilot order.

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
        "action": "delete_order",
        "proposal": {
            "order_id": order_id,
        },
    })


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


@tool
def delete_follow_up_task(
    task_id: int,
    runtime: ToolRuntime,
) -> Dict[str, Any]:
    """
    Propose deletion of an existing follow-up task.

    This does NOT modify the database.
    The proposal must be explicitly approved by a human
    before execution.
    """
    role = runtime.state.get("role")

    try:
        require_permission(role, Permission.MANAGE_FOLLOW_UP_TASKS)
    except PermissionError as error:
        return f"Access denied: {error}"

    return json.dumps({
        "action": "delete_follow_up_task",
        "proposal": {
            "task_id": task_id,
        },
    })


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


proposal_tools = [
    create_ticket,
    update_ticket,
    delete_ticket,
    create_order,
    update_order,
    delete_order,
    create_follow_up_task,
    update_follow_up_task,
    delete_follow_up_task,
    create_staff,
    update_staff,
    delete_staff,
]
