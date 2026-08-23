from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from .prompts import STRUCTURED_DATA_SYSTEM_PROMPT
from .states import StructuredDataState
from .tools import execute_sql

load_dotenv()

# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools([execute_sql])
llm = ChatOpenAI(model="gpt-5.6-luna", reasoning_effort="none").bind_tools([execute_sql])


def structured_data_agent(state: StructuredDataState) -> dict:
    """
    Call the SQL-tool-bound LLM for one retrieval step.

    The instruction is sent as a human message together with prior
    tool results so the model can iterate on queries.

    Args:
        state: Structured-data subgraph state with `instruction`
            and `messages`.

    Returns:
        A state update containing the model response.
    """
    message_history = state.get("messages", [])
    instruction = state.get("instruction", "")

    messages = [
        SystemMessage(content=STRUCTURED_DATA_SYSTEM_PROMPT),
        HumanMessage(content=instruction),
    ] + message_history

    response = llm.invoke(messages)

    return {"messages": [response]}