import json
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END
from langgraph.types import interrupt

from .prompts import AGENT_SYSTEM_PROMPT
from .states import AgentState
from .tools import all_tools
from .utils import (
    create_staff_in_database,
    create_task_in_database,
    delete_staff_in_database,
    update_staff_in_database,
)

load_dotenv()

model = ChatOpenAI(
    model="gpt-5.6-luna",
    reasoning_effort="none",
)
llm = model.bind_tools(all_tools)

APPROVAL_WORDS = {"yes", "approve", "approved", "confirm"}

SUPPORTED_ACTIONS = {
    "create_follow_up_task",
    "create_staff",
    "update_staff",
    "delete_staff",
}



def human_node(state: AgentState):
    human_input = interrupt("Please enter your input: ")

    return {"messages": [HumanMessage(content=human_input, name="human")]}


def route_human(state: AgentState) -> Literal[END, "perform_action", "agent"]:
    human_input = state.get("messages", [])[-1].content

    if human_input.strip().lower() == "exit":
        return END

    if state.get("pending_action"):
        normalized = human_input.strip().lower()

        if normalized in APPROVAL_WORDS:
            return "perform_action"

    return "agent"


def agent_node(state: AgentState):
    message_history = state.get("messages", [])

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPT),
    ] + message_history

    response = llm.invoke(messages)

    return {
        "messages": [response],
    }


def process_tool_result(state: AgentState):
    last_message = state.get("messages", [])[-1]

    # Only process tool outputs.
    if last_message.type != "tool":
        return {}

    content = (last_message.content or "").strip()

    if not content.startswith("{"):
        return {}

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return {}

    action = result.get("action")
    proposal = result.get("proposal")

    if action not in SUPPORTED_ACTIONS:
        return {}

    if not isinstance(proposal, dict):
        return {}

    return {
        "pending_action": {
            "action": action,
            "proposal": proposal,
        }
    }


def perform_action(state: AgentState):

    action = state.get("pending_action")

    if not action:
        return {}

    action_type = action.get("action")
    proposal = action.get("proposal", {})

    # -----------------------------------------------------
    # Create follow-up task
    # -----------------------------------------------------

    if action_type == "create_follow_up_task":

        task_id = create_task_in_database(
            title=proposal["title"],
            description=proposal["description"],
            priority=proposal["priority"],
            assigned_team=proposal["assigned_team"],
            ticket_id=proposal.get("ticket_id"),
            order_id=proposal.get("order_id"),
        )

        return {
            "pending_action": None,
            "messages": [
                AIMessage(
                    content=f"Follow-up task created: {task_id}"
                )
            ],
        }

    # -----------------------------------------------------
    # Create staff
    # -----------------------------------------------------

    if action_type == "create_staff":

        user_id = create_staff_in_database(
            name=proposal["name"],
            role=proposal["role"],
        )

        return {
            "pending_action": None,
            "messages": [
                AIMessage(
                    content=(
                        f"Staff member created successfully. "
                        f"User ID: {user_id}"
                    )
                )
            ],
        }

    # -----------------------------------------------------
    # Update staff
    # -----------------------------------------------------

    if action_type == "update_staff":

        update_staff_in_database(
            user_id=proposal["user_id"],
            name=proposal.get("name"),
            role=proposal.get("role"),
        )

        return {
            "pending_action": None,
            "messages": [
                AIMessage(
                    content=(
                        f"Staff member "
                        f"{proposal['user_id']} "
                        f"updated successfully."
                    )
                )
            ],
        }

    # -----------------------------------------------------
    # Delete staff
    # -----------------------------------------------------

    if action_type == "delete_staff":

        if state.get("user_id") == proposal["user_id"]:
            return {
                "pending_action": None,
                "messages": [
                    AIMessage(
                        content="Operation denied: you cannot delete your own staff account."
                    )
                ],
            }

        delete_staff_in_database(
            user_id=proposal["user_id"],
        )

        return {
            "pending_action": None,
            "messages": [
                AIMessage(
                    content=(
                        f"Staff member "
                        f"{proposal['user_id']} "
                        f"deleted successfully."
                    )
                )
            ],
        }

    # -----------------------------------------------------
    # Unknown action
    # -----------------------------------------------------

    return {
        "pending_action": None,
        "messages": [
            AIMessage(
                content=f"Unsupported action: {action_type}"
            )
        ],
    }
