from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import STRUCTURED_DATA_SYSTEM_PROMPT
from .schema import StructuredDataState
from .tools import execute_sql

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash").bind_tools([execute_sql])


def structured_data_agent(state: StructuredDataState) -> dict:
    message_history = state.get("messages", [])
    instruction = state.get("instruction", "")

    messages = [
        SystemMessage(content=STRUCTURED_DATA_SYSTEM_PROMPT),
        HumanMessage(content=instruction),
    ] + message_history

    response = llm.invoke(messages)

    return {"messages": [response]}