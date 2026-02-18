from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.memory import long_term_memory


@tool
def get_user_context(query: str, state: Annotated[dict, InjectedState]) -> str:
    """
    Search and retrieve past conversations with a specific user. Always use this tool to tailor your response to a specific user
    Formulate your query as a question and try to be specific.
    """

    # Retrieve relevant memories
    memories = long_term_memory.search(query=query, user_id=state["user_id"])

    context = "Relevant information from previous conversations:\n"
    for memory in memories:
        context += f"- {memory['memory']}\n"

    return context


user_context_tools = [get_user_context]
