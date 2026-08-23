from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from .states import ActionProposalState, ActionProposal
from .prompts import ACTION_PROPOSAL_SYSTEM_PROMPT, STRUCTURE_PROPOSAL_SYSTEM_PROMPT
from .tools import proposal_tools

llm = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")

proposal_llm = llm.bind_tools(proposal_tools)
structured_llm = llm.with_structured_output(ActionProposal)


def create_proposal(state: ActionProposalState):
    """
    Determine which action proposal should be created and call the
    appropriate proposal tool.

    This node only creates a proposal. It never executes the action
    or modifies the database.
    """
    try:
        message_history = state.get("messages", [])
        instruction = state.get("instruction", "")

        messages = [
            SystemMessage(content=ACTION_PROPOSAL_SYSTEM_PROMPT),
            HumanMessage(content=instruction),
        ] + message_history

        response = proposal_llm.invoke(messages)

        return {
            "messages": [response],
            "error": None,
        }

    except Exception as error:
        return {
            "error": f"Failed to create action proposal: {error}",
        }


def structure_proposal(state: ActionProposalState):
    """
    Convert the proposal tool result into a validated ActionProposal.

    This node does not execute the proposed action.
    """
    try:
        messages = state.get("messages", [])

        if not messages:
            return {
                "error": "No proposal tool result was produced."
            }

        last_message = messages[-1].content

        structure_messages = [
            SystemMessage(content=STRUCTURE_PROPOSAL_SYSTEM_PROMPT),
            HumanMessage(content=last_message),
        ]

        result = structured_llm.invoke(structure_messages)

        return {
            "action": result.action,
            "proposal": result.proposal,
            "error": None,
        }

    except Exception as error:
        return {
            "error": f"Failed to structure action proposal: {error}",
        }