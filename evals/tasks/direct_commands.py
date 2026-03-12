import json

from datasets import direct_commands_dataset
from graders.deterministic import DeviceStateCorrectness
from metrics import make_pass_all_k, make_pass_at_k

from agent import run_agent
from tasks.base import EvalTask


def build_items():
    return [
        {
            "input": (value[1], value[0]),
            "expected_output": json.dumps(value[2]),
            "tags": value[3][0],
        }
        for value in direct_commands_dataset
    ]


def task_fn(dataset_item):
    try:
        command = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected = json.loads(dataset_item["expected_output"])

        result = run_agent(home_template, command)
        home_state = result["home_state"]

        return {
            "input": (command, home_template),
            "output": "",  # not used by code graders
            "expected_output": json.dumps(expected),
            "home_state": home_state,
        }
    except Exception as e:
        return {"input": dataset_item.get("input", {}), "error": str(e)}


task = EvalTask(
    experiment_name="DirectCommandsExperiment",
    description="Evaluates the agent's ability to correctly execute direct commands.",
    dataset_name="direct_commands_dataset",
    dataset_items=build_items(),
    task_fn=task_fn,
    metrics=[DeviceStateCorrectness()],
    # @TODO: improve how pass k
    experiment_scoring_functions=[
        make_pass_at_k(k=1, metric_name=DeviceStateCorrectness().name),
        make_pass_all_k(k=2, metric_name=DeviceStateCorrectness().name),
    ],
)
