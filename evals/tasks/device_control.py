import json

from datasets import (
    command_chaining_dataset,
    device_resolution_dataset,
    direct_commands_dataset,
    intent_resolution_dataset,
)
from graders.deterministic import DeviceStateCorrectness
from graders.model_based import intent_relevance_grader

from agent import get_last_ai_response, run_agent
from tasks.base import EvalTask

_METRICS = [DeviceStateCorrectness()]


def _build_items(dataset):
    return [
        {
            "input": (value[1], value[0]),
            "expected_output": json.dumps(value[2]),
            "tags": value[3][0],
        }
        for value in dataset
    ]


def task_fn(dataset_item):
    try:
        command = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected = json.loads(dataset_item["expected_output"])

        result = run_agent(home_template, command)

        return {
            "input": command,
            "output": get_last_ai_response(result),
            "expected_output": json.dumps(expected),
            "home_state": result["home_state"],
        }
    except Exception as e:
        return {"input": dataset_item.get("input", {}), "output": "", "error": str(e)}


direct_commands_task = EvalTask(
    experiment_name="DirectCommandsExperiment",
    description="Evaluates the agent's ability to correctly execute direct commands.",
    dataset_name="direct_commands_dataset",
    dataset_items=_build_items(direct_commands_dataset),
    task_fn=task_fn,
    metrics=_METRICS,
)

device_resolution_task = EvalTask(
    experiment_name="DeviceResolutionExperiment",
    description="Evaluates the agent's ability to resolve ambiguous device references.",
    dataset_name="device_resolution_dataset",
    dataset_items=_build_items(device_resolution_dataset),
    task_fn=task_fn,
    metrics=_METRICS,
)

command_chaining_task = EvalTask(
    experiment_name="CommandChainingExperiment",
    description="Evaluates the agent's ability to execute multiple commands in sequence.",
    dataset_name="command_chaining_dataset",
    dataset_items=_build_items(command_chaining_dataset),
    task_fn=task_fn,
    metrics=_METRICS,
)


intent_resolution_task = EvalTask(
    experiment_name="IntentResolutionExperiment",
    description="Evaluates the agent's ability to resolve ambiguous user intent.",
    dataset_name="intent_resolution_dataset",
    dataset_items=_build_items(intent_resolution_dataset),
    task_fn=task_fn,
    metrics=[DeviceStateCorrectness(), intent_relevance_grader],
)
