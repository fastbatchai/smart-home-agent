import asyncio
import json
import uuid
from datetime import datetime

from rich.console import Console

from src.agent import create_agent_graph

# Initialize Rich console
console = Console()


async def main():
    # Generate a unique thread ID each time the script runs
    thread_id = (
        f"thread-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    )

    with open("./data/home_templates/h1.json", "r") as f:
        initial_home_state = json.load(f)
        initial_home_state = initial_home_state["devices"]

    agent_graph = create_agent_graph().compile()
    # tracer = OpikTracer(graph=agent_graph.get_graph(xray=True), thread_id=thread_id)
    config = {  # "callbacks": [tracer],
        "configurable": {"thread_id": thread_id}
    }

    # Initialize state with empty messages and home state
    state = {"messages": [], "home_state": initial_home_state}

    # Welcome banner
    console.print()
    console.print("[bold cyan]🏠 Smart Home Agent[/bold cyan]")
    console.print(f"[dim]Conversation ID: {thread_id}[/dim]")
    console.print("[dim]Type 'exit', 'quit', or 'bye' to end the conversation.[/dim]\n")

    # Track the number of messages we've already printed
    printed_message_count = 0

    while True:
        # Get user input
        console.print()
        user_input = console.input("[bold green]You:[/bold green] ").strip()

        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "bye"]:
            console.print("\n[bold cyan]Goodbye![/bold cyan]\n")
            break

        if not user_input:
            continue

        # Add user message to state
        state["messages"].append(user_input)

        # Invoke agent with current state
        result = await agent_graph.ainvoke(state, config=config)

        # Update state with result messages and home state
        state = result

        # Print all new messages that came from this interaction
        new_messages = result["messages"][
            printed_message_count + 1 :
        ]  # Skip the human message we just printed

        for message in new_messages:
            if message.type == "ai":
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

        # Update the count of printed messages
        printed_message_count = len(result["messages"])


if __name__ == "__main__":
    asyncio.run(main())
