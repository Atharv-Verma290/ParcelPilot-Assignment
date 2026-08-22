import json

import streamlit as st

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langgraph.types import Command

from graphs.main_graph.graph import build_graph
from graphs.main_graph.states import AgentState


st.set_page_config(
    page_title="ParcelPilot Support Agent",
    page_icon="📦",
    layout="wide",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "streamlit-session"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "waiting_for_input" not in st.session_state:
    st.session_state.waiting_for_input = False

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def format_as_markdown(value) -> str:
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, default=str)

    text = str(value).strip()

    try:
        parsed = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text

    if isinstance(parsed, (dict, list)):
        return json.dumps(parsed, indent=2, default=str)

    return text


def display_message(message):
    """Display a LangChain message in the chat UI, in graph order."""

    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content or "")

    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            if message.content:
                st.markdown(message.content)

            for tool_call in message.tool_calls or []:
                args = format_as_markdown(tool_call.get("args", {}))
                with st.expander(
                    f"🔧 Tool call — `{tool_call['name']}`",
                    expanded=True,
                ):
                    st.markdown(args)

    elif isinstance(message, ToolMessage):
        with st.chat_message("assistant"):
            output = format_as_markdown(message.content)
            with st.expander(
                f"📦 Tool output — `{message.name or 'tool'}`",
                expanded=True,
            ):
                st.markdown(output)


def get_graph_config():
    return {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


def sync_messages_from_graph(output) -> None:
    graph_messages = output.get("messages", [])
    st.session_state.messages = [
        message
        for message in graph_messages
        if isinstance(message, (HumanMessage, AIMessage, ToolMessage))
    ]


def process_graph_input(user_input: str):
    graph = st.session_state.graph
    config = get_graph_config()

    if st.session_state.waiting_for_input:
        output = graph.invoke(
            Command(resume=user_input),
            config,
        )
    else:
        input_state: AgentState = {
            "messages": [
                HumanMessage(content=user_input)
            ]
        }
        output = graph.invoke(input_state, config)

    snapshot = graph.get_state(config)
    st.session_state.waiting_for_input = bool(snapshot.next)

    return output


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.title("📦 ParcelPilot Support & Operations Agent")

st.caption(
    "Internal support assistant • "
    "Structured data + document retrieval + follow-up actions"
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("Debug")

    st.text_input(
        "Thread ID",
        key="thread_id",
    )

    st.divider()

    st.write("### Current state")

    if st.session_state.waiting_for_input:
        st.warning("Waiting for human input")
    else:
        st.success("Agent active")

    st.write(
        f"Messages: {len(st.session_state.messages)}"
    )


# ---------------------------------------------------------
# Display conversation
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

    with st.spinner("Agent is working..."):

        try:
            output = process_graph_input(user_input)
            sync_messages_from_graph(output)
            st.rerun()

        except Exception as e:

            st.error(
                f"Graph execution failed:\n\n{e}"
            )
