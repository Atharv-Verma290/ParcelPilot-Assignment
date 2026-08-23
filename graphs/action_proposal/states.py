from typing import Annotated, Any, Dict, Literal, Optional, Union
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

class ActionProposalState(MessagesState):
    instruction: str

    # Populated once the proposal agent determines the action.
    action: Optional[str] = None

    # Structured parameters for the proposed action.
    proposal: Dict[str, Any] 

    # Context inherited from the main agent.
    user_id: str
    role: str

    # Used when proposal generation fails.
    error: Optional[str] = None


# ============================================================
# Ticket
# ============================================================

class CreateTicketProposal(BaseModel):
    account_id: str
    subject: str
    description: str
    channel: Literal["email", "chat"]
    status: Literal["open", "closed"] = "open"
    assigned_to: Optional[str] = None

class UpdateTicketProposal(BaseModel):
    ticket_id: str
    subject: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["open", "closed"]] = None
    assigned_to: Optional[str] = None

class DeleteTicketProposal(BaseModel):
    ticket_id: str


# ============================================================
# Order
# ============================================================

class CreateOrderProposal(BaseModel):
    account_id: str
    carrier: str
    shipment_fee_inr: int
    status: Literal["BOOKED", "PICKED_UP", "DELIVERED", "CANCELLED"] = "BOOKED"
    booked_at: Optional[str] = None
    pickup_window_start: Optional[str] = None
    pickup_window_end: Optional[str] = None
    notes: Optional[str] = None

class UpdateOrderProposal(BaseModel):
    order_id: str
    carrier: Optional[str] = None
    status: Optional[Literal["BOOKED", "PICKED_UP", "DELIVERED", "CANCELLED"]] = None
    pickup_window_start: Optional[str] = None
    pickup_window_end: Optional[str] = None
    pickup_actual_at: Optional[str] = None
    shipment_fee_inr: Optional[float] = None
    carrier_fault: Optional[bool] = None
    customer_fault: Optional[bool] = None
    cancellation_requested_at: Optional[str] = None
    notes: Optional[str] = None

class DeleteOrderProposal(BaseModel):
    order_id: str


# ============================================================
# Follow-up task
# ============================================================

class CreateFollowUpTaskProposal(BaseModel):
    title: str
    description: str
    priority: Literal["LOW", "MEDIUM", "HIGH", "URGENT"]
    assigned_team: str
    ticket_id: Optional[str] = None
    order_id: Optional[str] = None

class UpdateFollowUpTaskProposal(BaseModel):
    task_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["LOW", "MEDIUM", "HIGH", "URGENT"]] = None
    assigned_team: Optional[str] = None
    status: Optional[Literal["OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"]] = None
    ticket_id: Optional[str] = None
    order_id: Optional[str] = None

class DeleteFollowUpTaskProposal(BaseModel):
    task_id: int


# ============================================================
# Staff
# ============================================================

class CreateStaffProposal(BaseModel):
    name: str
    role: Literal["ADMIN", "OPERATIONS", "SUPPORT"]

class UpdateStaffProposal(BaseModel):
    user_id: str
    name: Optional[str] = None
    role: Optional[Literal["SUPPORT", "OPERATIONS", "ADMIN"]] = None

class DeleteStaffProposal(BaseModel):
    user_id: str


# ============================================================
# ActionProposal
# ============================================================

class CreateTicketAction(BaseModel):
    action: Literal["create_ticket"]
    proposal: CreateTicketProposal

class UpdateTicketAction(BaseModel):
    action: Literal["update_ticket"]
    proposal: UpdateTicketProposal

class DeleteTicketAction(BaseModel):
    action: Literal["delete_ticket"]
    proposal: DeleteTicketProposal

class CreateOrderAction(BaseModel):
    action: Literal["create_order"]
    proposal: CreateOrderProposal

class UpdateOrderAction(BaseModel):
    action: Literal["update_order"]
    proposal: UpdateOrderProposal

class DeleteOrderAction(BaseModel):
    action: Literal["delete_order"]
    proposal: DeleteOrderProposal

class CreateFollowUpTaskAction(BaseModel):
    action: Literal["create_follow_up_task"]
    proposal: CreateFollowUpTaskProposal

class UpdateFollowUpTaskAction(BaseModel):
    action: Literal["update_follow_up_task"]
    proposal: UpdateFollowUpTaskProposal

class DeleteFollowUpTaskAction(BaseModel):
    action: Literal["delete_follow_up_task"]
    proposal: DeleteFollowUpTaskProposal

class CreateStaffAction(BaseModel):
    action: Literal["create_staff"]
    proposal: CreateStaffProposal

class UpdateStaffAction(BaseModel):
    action: Literal["update_staff"]
    proposal: UpdateStaffProposal

class DeleteStaffAction(BaseModel):
    action: Literal["delete_staff"]
    proposal: DeleteStaffProposal


ActionProposalData = Annotated[
    Union[
        CreateTicketAction,
        UpdateTicketAction,
        DeleteTicketAction,
        CreateOrderAction,
        UpdateOrderAction,
        DeleteOrderAction,
        CreateFollowUpTaskAction,
        UpdateFollowUpTaskAction,
        DeleteFollowUpTaskAction,
        CreateStaffAction,
        UpdateStaffAction,
        DeleteStaffAction,
    ],
    Field(
        discriminator="action",
        description=(
            "A structured proposal for an operational action. The proposal "
            "contains the action to be performed and the parameters required "
            "to execute the action."
        )
    )
]


ACTION_SCHEMAS = {
    "create_ticket": CreateTicketAction,
    "update_ticket": UpdateTicketAction,
    "delete_ticket": DeleteTicketAction,

    "create_order": CreateOrderAction,
    "update_order": UpdateOrderAction,
    "delete_order": DeleteOrderAction,

    "create_follow_up_task": CreateFollowUpTaskAction,
    "update_follow_up_task": UpdateFollowUpTaskAction,
    "delete_follow_up_task": DeleteFollowUpTaskAction,

    "create_staff": CreateStaffAction,
    "update_staff": UpdateStaffAction,
    "delete_staff": DeleteStaffAction,
}