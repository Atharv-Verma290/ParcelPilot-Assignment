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
from .utils import create_task_in_database

load_dotenv()

model = ChatOpenAI(
    model="gpt-5.6-luna",
    reasoning_effort="none",
)
llm = model.bind_tools(all_tools)

APPROVAL_WORDS = {"yes", "approve", "approved", "confirm"}


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

    if last_message.name != "create_follow_up_task":
        return {}

    content = (last_message.content or "").strip()

    if not content.startswith("{"):
        return {}

    try:
        proposal = json.loads(content)
    except json.JSONDecodeError:
        return {}

    return {
        "pending_action": {
            "action": "create_follow_up_task",
            "proposal": proposal,
        }
    }


def perform_action(state: AgentState):
    action = state.get("pending_action", {})

    if not action:
        return {}

    if action["action"] == "create_follow_up_task":
        proposal = action["proposal"]

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
            "messages": [AIMessage(content=f"Follow-up task created: {task_id}")],
        }

    return {}
