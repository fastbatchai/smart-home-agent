import asyncio
import json
import uuid

from langchain_core.messages import AIMessage, ToolMessage
from opik import track

from src.agent import create_agent_graph
from src.config import config
from src.memory import long_term_memory


@track
async def _run_agent_async(initial_home_state, command, user_id, user_name, thread_id):

    agent_graph = create_agent_graph().compile()

    state = {
        "messages": [command],
        "home_state": initial_home_state,
        "user_name": user_name,
        "user_id": user_id,
        "thread_id": thread_id,
    }
    configuration = {"configurable": {"user_id": user_id, "thread_id": thread_id}}

    return await agent_graph.ainvoke(state, config=configuration)


def cleanup_memories(user_id: str) -> None:
    """Delete all Mem0 memories for the given user after the test."""
    long_term_memory.delete_all(user_id=user_id)


def initialize_home_state(home_template: str) -> dict:
    if config.TEST_MODE:
        with open(f"./data/home_templates/{home_template}.json") as f:
            return json.load(f)["devices"]
    else:
        # TODO: Initialize the home state from the Device Service API
        return None


def run_agent(
    home_template,
    command,
    user_id="eval-user-01",
    user_name="eval-user-01",
    thread_id=None,
):
    """The agent should run in an isolated environment with no shared state between runs.
    This means:
    1- Each run should have a unique thread ID to avoid short-term memory leakage between run
    2- The long-term memory should be cleared
    3- All runs use the same original home state
    """

    if thread_id is None:
        thread_id = str(uuid.uuid4())

    # make sure that the long-term memory is cleared
    cleanup_memories(user_id)

    # initialize the home state
    # In prod env, this should be replaced with a call to the Device Service API
    initial_home_state = initialize_home_state(home_template)

    return asyncio.run(
        _run_agent_async(initial_home_state, command, user_id, user_name, thread_id)
    )


def get_last_ai_response(result):
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            return message.content
    return ""


def extract_called_tools(result):
    tools = []
    for message in result["messages"]:
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                tools.append(tc["name"] if isinstance(tc, dict) else tc.name)
    return tools


def extract_n_turns(result) -> int:
    """Number of LLM calls (AIMessages) in the conversation."""
    return sum(1 for m in result["messages"] if isinstance(m, AIMessage))


def extract_n_tool_calls(result) -> int:
    """Total number of individual tool calls made."""
    return sum(
        len(m.tool_calls)
        for m in result["messages"]
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
    )


def extract_memory_context(result):
    contexts = []
    for message in result["messages"]:
        if isinstance(message, ToolMessage) and message.name == "get_user_context":
            contexts.append(message.content)
    return "\n".join(contexts)
