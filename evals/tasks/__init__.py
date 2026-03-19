from tasks.device_control import (
    command_chaining_task,
    device_resolution_task,
    direct_commands_task,
    intent_resolution_task,
)
from tasks.memory_retrieval import task as memory_retrieval_task
from tasks.tool_selection import task as tool_selection_task

all_tasks = [
    direct_commands_task,
    device_resolution_task,
    command_chaining_task,
    intent_resolution_task,
    tool_selection_task,
    memory_retrieval_task,
]
