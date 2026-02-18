from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import ToolNode

from src.config import config
from src.prompts import AGENT_SYSTEM_PROMPT
from src.state import AgentState
from src.tools import all_tools

# Create tool node with a descriptive name
tool_node = ToolNode(all_tools, name="SmartHomeTools")


def get_chat_model(
    temperature: float = 0.7, model_name: str = config.GROQ_LLM_MODEL
) -> BaseChatModel:
    """Create and return a ChatGroq model instance"""
    if config.LLM_PROVIDER.lower() == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            api_key=config.GROQ_API_KEY,
            model_name=model_name,
            temperature=temperature,
        )
    if config.LLM_PROVIDER.lower() == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=config.OPENAI_API_KEY,
            model_name=config.OPENAI_MODEL_NAME,
            temperature=temperature,
        )
    if config.LLM_PROVIDER.lower() == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=config.OLLAMA_MODEL_NAME,
            temperature=temperature,
        )


def get_response_chain():
    model = get_chat_model()
    # ChatOllama doesn't support parallel_tool_calls parameter
    if config.LLM_PROVIDER.lower() == "ollama":
        model = model.bind_tools(all_tools)
    else:
        model = model.bind_tools(all_tools, parallel_tool_calls=False)
    system_message = AGENT_SYSTEM_PROMPT
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ],
        template_format="f-string",
    )

    response = prompt | model

    return response


async def response_node(state: AgentState):
    conversation_chain = get_response_chain()

    response = await conversation_chain.ainvoke(
        {"current_home_state": state["home_state"], "messages": state["messages"]},
        config={"run_name": "LLM", "tags": ["agent_response"]},
    )

    return {"messages": response}
