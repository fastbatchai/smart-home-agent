from typing import Any

import httpx
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from opik.integrations.langchain import OpikTracer

from src.agent import create_agent_graph
from src.config import config


async def execute_agent(
    messages: str | list[str] | list[dict[str, Any]],
    user_id: str,
    user_name: str,
    session_id: str,
) -> tuple[str, dict[str, Any]]:

    # Request the current home state from the device service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{config.DEVICE_SERVICE_URL}/users/{user_id}/devices"
            )
            response.raise_for_status()
            initial_home_state = response.json()
            print(f"Initial home state: {initial_home_state}")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # User doesn't have devices yet - initialize them
                print(
                    f"No devices found for user {user_id}, initializing device state..."
                )
                init_response = await client.post(
                    f"{config.DEVICE_SERVICE_URL}/users/{user_id}/devices/initialize"
                )
                init_response.raise_for_status()
                response = await client.get(
                    f"{config.DEVICE_SERVICE_URL}/users/{user_id}/devices"
                )
                response.raise_for_status()
                initial_home_state = response.json()
                print(f"Initialized home state: {initial_home_state}")

    ttl_config = {
        "default_ttl": config.SESSION_WINDOW_SECONDS,  # Expire checkpoints after 60 minutes
        "refresh_on_read": True,  # Reset expiration time when reading checkpoints
    }

    builder = create_agent_graph()

    try:
        async with AsyncRedisSaver.from_conn_string(
            config.REDIS_DB_URI, ttl=ttl_config
        ) as checkpointer:
            await checkpointer.asetup()

            agent_graph = builder.compile(checkpointer=checkpointer)

            tracer = OpikTracer(graph=agent_graph.get_graph(xray=True))

            configuration = {
                "configurable": {"user_id": user_id, "thread_id": session_id},
                "callbacks": [tracer],
            }
            state = {
                "messages": messages,
                "home_state": initial_home_state,
                "user_name": user_name,
                "user_id": user_id,
                "thread_id": session_id,
            }

            result = await agent_graph.ainvoke(state, config=configuration)
        last_message = result["messages"][-1]
        print(last_message.content)
        print(f"Updated home state: {result['home_state']}")

        return last_message.content, result["home_state"]

    except Exception as e:
        raise RuntimeError(f"Error running the agent flow: {str(e)}") from e
