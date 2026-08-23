import json
import uuid

import streamlit as st

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.types import Command

from graphs.main_graph.graph import build_graph
from graphs.main_graph.states import AgentState

from auth.users import get_all_staff


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="ParcelPilot Support Agent",
    page_icon="📦",
    layout="wide",
)


# ---------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "waiting_for_input" not in st.session_state:
    st.session_state.waiting_for_input = False

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()


# ---------------------------------------------------------
# Staff
# ---------------------------------------------------------

staff = get_all_staff()

staff_by_name = {
    person["name"]: person
    for person in staff
}

staff_names = list(staff_by_name)


if (
    "selected_user" not in st.session_state
    or st.session_state.selected_user not in staff_by_name
):
    st.session_state.selected_user = (
        staff_names[0]
        if staff_names
        else ""
    )


# ---------------------------------------------------------
# Session helpers
# ---------------------------------------------------------

def start_new_thread():
    """
    Start a completely fresh conversation.

    A new thread ID means LangGraph uses a new checkpoint
    rather than continuing the previous conversation.
    """

    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.waiting_for_input = False


def switch_user():
    """
    Change the authenticated staff user.

    A user switch also starts a new conversation so that
    authenticated identity cannot be carried across users.
    """

    start_new_thread()


# ---------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------

def format_as_markdown(value) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(
            value,
            indent=2,
            default=str,
        )

    text = str(value).strip()

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text

    if isinstance(parsed, (dict, list)):
        return json.dumps(
            parsed,
            indent=2,
            default=str,
        )

    return text


# ---------------------------------------------------------
# Message display
# ---------------------------------------------------------

def display_message(message):
    """
    Display a LangChain message in graph execution order.

    AI messages display both the model response and any
    tool calls made by the model.

    Tool messages display the corresponding tool output.
    """

    if isinstance(message, HumanMessage):

        with st.chat_message("user"):
            st.markdown(
                message.content or ""
            )

    elif isinstance(message, AIMessage):

        with st.chat_message("assistant"):

            if message.content:
                st.markdown(message.content)

            for tool_call in message.tool_calls or []:

                args = format_as_markdown(
                    tool_call.get("args", {})
                )

                with st.expander(
                    f"🔧 Tool call — `{tool_call['name']}`",
                    expanded=True,
                ):
                    st.markdown(args)

    elif isinstance(message, ToolMessage):

        with st.chat_message("assistant"):

            output = format_as_markdown(
                message.content
            )

            with st.expander(
                f"📦 Tool output — "
                f"`{message.name or 'tool'}`",
                expanded=True,
            ):
                st.markdown(output)


# ---------------------------------------------------------
# Graph helpers
# ---------------------------------------------------------

def get_graph_config():
    return {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


def sync_messages_from_graph(output) -> None:
    """
    Synchronize visible Streamlit messages with the
    messages returned by LangGraph.
    """

    graph_messages = output.get(
        "messages",
        []
    )

    st.session_state.messages = [
        message
        for message in graph_messages
        if isinstance(
            message,
            (
                HumanMessage,
                AIMessage,
                ToolMessage,
            ),
        )
    ]


# ---------------------------------------------------------
# Graph execution
# ---------------------------------------------------------

def process_graph_input(user_input: str):

    graph = st.session_state.graph

    user = staff_by_name[
        st.session_state.selected_user
    ]

    config = get_graph_config()

    # -----------------------------------------------------
    # Resume an interrupted graph
    # -----------------------------------------------------

    if st.session_state.waiting_for_input:

        output = graph.invoke(
            Command(
                resume=user_input
            ),
            config,
        )

    # -----------------------------------------------------
    # Start a new graph execution
    # -----------------------------------------------------

    else:

        input_state: AgentState = {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],

            # Authentication context is injected here.
            # The LLM does not provide these values.
            "user_id": user["user_id"],
            "role": user["role"],
        }

        output = graph.invoke(
            input_state,
            config,
        )

    # -----------------------------------------------------
    # Check whether the graph is waiting for human input
    # -----------------------------------------------------

    snapshot = graph.get_state(config)

    st.session_state.waiting_for_input = bool(
        snapshot.next
    )

    return output


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.title(
    "📦 ParcelPilot Support & Operations Agent"
)

st.caption(
    "Internal support assistant • "
    "Structured data + document retrieval + follow-up actions"
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Session")

    # -----------------------------------------------------
    # Staff selection
    # -----------------------------------------------------

    if not staff_names:

        st.error(
            "No staff records found."
        )

    else:

        st.selectbox(
            "Logged in as",
            staff_names,
            key="selected_user",
            on_change=switch_user,
        )

        user = staff_by_name[
            st.session_state.selected_user
        ]

        st.write(
            f"**User ID:** {user['user_id']}"
        )

        st.write(
            f"**Role:** {user['role']}"
        )

    # -----------------------------------------------------
    # New conversation
    # -----------------------------------------------------

    if st.button(
        "🆕 New conversation",
        use_container_width=True,
    ):

        start_new_thread()

        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # Debug information
    # -----------------------------------------------------

    st.header("Debug")

    st.write("**Thread ID:**")

    st.code(
        st.session_state.thread_id
    )

    st.divider()

    st.write("### Current state")

    if st.session_state.waiting_for_input:

        st.warning(
            "Waiting for human input"
        )

    else:

        st.success(
            "Agent active"
        )

    st.write(
        f"Messages: "
        f"{len(st.session_state.messages)}"
    )


# ---------------------------------------------------------
# Conversation
# ---------------------------------------------------------

for message in st.session_state.messages:

    display_message(message)


# ---------------------------------------------------------
# User input
# ---------------------------------------------------------

user_input = st.chat_input(
    "Ask ParcelPilot Support Agent..."
)


if user_input:

    with st.spinner(
        "Agent is working..."
    ):

        try:

            output = process_graph_input(
                user_input
            )

            sync_messages_from_graph(
                output
            )

            st.rerun()

        except Exception as e:

            st.error(
                "Graph execution failed:\n\n"
                f"{e}"
            )