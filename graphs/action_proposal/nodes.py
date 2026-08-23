from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from .states import ActionProposalState, ActionProposal
from .prompts import ACTION_PROPOSAL_SYSTEM_PROMPT

llm = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")
proposal_llm = llm.with_structured_output(ActionProposal)

def create_proposal(state: ActionProposalState) -> dict:
    """
    Convert the requested action into a normalized action proposal.

    This node MUST NOT modify application state or the database.
    """

    instruction = state["instruction"]

    # For now, this can be implemented using an LLM
    # or deterministic logic depending on the action.

    return {
        "proposal": {
            "instruction": instruction
        }
    }


def build_action_proposal(state: ActionProposalState):

    messages = [
        SystemMessage(content=ACTION_PROPOSAL_SYSTEM_PROMPT),
        HumanMessage(content=state["instruction"]),
    ]

    result = proposal_llm.invoke(messages)

    return {
        "action": result.action,
        "proposal": result.proposal,
    }