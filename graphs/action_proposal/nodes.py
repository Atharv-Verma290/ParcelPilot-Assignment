import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from .states import ACTION_SCHEMAS, ActionProposalState, ActionProposal
from .prompts import ACTION_PROPOSAL_SYSTEM_PROMPT, STRUCTURE_PROPOSAL_SYSTEM_PROMPT
from .tools import proposal_tools

llm = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none")

proposal_llm = llm.bind_tools(proposal_tools)
# structured_llm = llm.with_structured_output(ActionProposal)


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

        if not response.tool_calls:
            return {
                "messages": [response],
                "error": "Proposal agent did not call an action proposal tool."
            }
        
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

        if isinstance(last_message, str):
            data = json.loads(last_message)
        else:
            data = last_message 

        action = data.get("action")
        if not action:
            return {
                "error": "Proposal tool result did not contain an action."
            }
        
        schema = ACTION_SCHEMAS.get(action)
        if schema is None:
            return {
                "error": f"Unsupported proposal action: {action}"
            }
        
        # Dynamically bind the schema to the structured LLM.
        structured_llm = llm.with_structured_output(schema)

        structure_messages = [
            SystemMessage(content=STRUCTURE_PROPOSAL_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(data)),
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