import asyncio
import json
import uuid

from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from opik.integrations.langchain import OpikTracer
from rich.console import Console

from src.agent import create_agent_graph
from src.config import config
from src.memory import generate_thread_id

# Initialize Rich console
console = Console()


async def main():

    with open("./data/home_templates/h1.json", "r") as f:
        initial_home_state = json.load(f)
        initial_home_state = initial_home_state["devices"]

    user_name = "Alice"
    user_id = f"Alice-{uuid.uuid5(uuid.NAMESPACE_DNS, user_name)}"
    thread_id = generate_thread_id(user_id=user_id)
    ttl_config = {
        "default_ttl": config.SESSION_WINDOW_SECONDS,  # Expire checkpoints after 60 minutes
        "refresh_on_read": True,  # Reset expiration time when reading checkpoints
    }

    command = console.input("[bold green]You:[/bold green] ").strip()

    console.print()
    console.print("[bold cyan]🏠 Smart Home Agent - Single Command Mode[/bold cyan]")
    console.print(f"[dim]User: {user_name}[/dim]")
    console.print(f"[dim]Thread ID: {thread_id}[/dim]")
    console.print()

    async with AsyncRedisSaver.from_conn_string(
        config.REDIS_DB_URI, ttl=ttl_config
    ) as checkpointer:
        await checkpointer.asetup()

        agent_graph = create_agent_graph().compile(checkpointer=checkpointer)
        tracer = OpikTracer(
            project_name="smart-home-agent",
            graph=agent_graph.get_graph(xray=True),
        )
        configuration = {
            "callbacks": [tracer],
            "configurable": {
                "thread_id": thread_id,
                "user_id": user_id,
            },
        }
        state = {
            "messages": [command],
            "home_state": initial_home_state,
            "user_name": user_name,
            "user_id": user_id,
            "thread_id": thread_id,
        }

        # Print the user command
        console.print(f"[bold green]You:[/bold green] [green]{command}[/green]\n")

        result = await agent_graph.ainvoke(state, config=configuration)

    # Print all messages with colors
    for message in result["messages"][
        1:
    ]:  # Skip the first message (user input we already printed)
        if message.type == "human":
            console.print(
                f"\n[bold green]You:[/bold green] [green]{message.content}[/green]"
            )

        elif message.type == "ai":
            # Check if this AI message has tool calls
            if hasattr(message, "tool_calls") and message.tool_calls:
                # Print AI thinking (if any content)
                if message.content:
                    console.print(
                        f"\n[bold blue]Assistant:[/bold blue] [blue]{message.content}[/blue]"
                    )

                # Print tool calls
                for tool_call in message.tool_calls:
                    console.print(
                        f"\n[bold yellow]Tool:[/bold yellow] [yellow]{tool_call['name']}[/yellow]"
                    )
                    # console.print(
                    #     f"[dim yellow]{json.dumps(tool_call['args'], indent=2)}[/dim yellow]"
                    # )
            else:
                # Regular AI message
                console.print(
                    f"\n[bold blue]Assistant:[/bold blue] [blue]{message.content}[/blue]"
                )

        elif message.type == "tool":
            # Tool response
            tool_name = getattr(message, "name", "Unknown Tool")
            content = message.content

            # Truncate long responses for readability
            if len(content) > 500:
                content = content[:500] + "... (truncated)"

            console.print(
                f"[bold magenta]Tool Response ({tool_name}):[/bold magenta] [dim magenta]{content}[/dim magenta]"
            )

    console.print()


if __name__ == "__main__":
    asyncio.run(main())
