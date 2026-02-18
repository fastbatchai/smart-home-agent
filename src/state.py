from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    Represents the shared state for the agent during execution.

    The `AgentState` object acts as a central data store that nodes within the
    agent's execution graph can read from and write to. It persists across node
    transitions, allowing information to be passed between LLM calls, tools,
    and other computation steps.
    """

    home_state: dict[str, str]
    user_name: str
    user_id: str
    thread_id: str


def state_to_str__(state: AgentState):
    """
    Convert a state object to a str.
    Can't define an __str__ method because MessageState is a TypedDict
    """
    if "messages" in state and bool(state["messages"]):
        conversation = state["messages"]
    else:
        conversation = ""

    return f"""home state={state["home_state"]},
user name={state["user_name"]},
user id={state["user_id"]},
thread id={state["thread_id"]},
conversation={conversation})
        """
