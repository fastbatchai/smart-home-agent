from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from src.nodes import response_node, tool_node
from src.state import AgentState


@lru_cache(maxsize=1)
def create_agent_graph() -> StateGraph:
    """
    Build and return the execution graph for the agent.

    This function defines the structure of the agent's state graph, including
    the nodes (LLMs, tools, or custom functions) and the edges that determine
    how the agent transitions between them. The resulting graph controls the
    agent's reasoning flow, tool usage, and data passing between components.
    """

    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("response_node", response_node)
    graph_builder.add_node("tool_node", tool_node)

    graph_builder.add_edge(START, "response_node")

    graph_builder.add_conditional_edges(
        "response_node", tools_condition, {"tools": "tool_node", END: END}
    )
    graph_builder.add_edge("tool_node", "response_node")
    graph_builder.add_edge("response_node", END)

    return graph_builder
