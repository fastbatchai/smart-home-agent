import json

from datasets import tool_selection_dataset
from graders.deterministic import ToolSelectionQuality, AgentPlanEfficiency
from graders.model_based import tool_appropriateness_grader
from metrics import make_pass_all_k, make_pass_at_k

from agent import extract_called_tools, run_agent
from tasks.base import EvalTask


def build_items():
    return [
        {
            "input": (value[1], value[0]),
            "expected_output": json.dumps(value[2]),
            "forbidden_tools": json.dumps(value[3]),
            "tags": value[4][0],
        }
        for value in tool_selection_dataset
    ]


def task_fn(dataset_item):
    try:
        command = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected_tools = json.loads(dataset_item["expected_output"])
        forbidden_tools = json.loads(dataset_item.get("forbidden_tools", "[]"))

        result = run_agent(home_template, command)
        called_tools = extract_called_tools(result)

        return {
            "input": command,
            "output": called_tools,
            "expected_output": expected_tools,
            "forbidden_tools": forbidden_tools,
        }
    except Exception as e:
        return {"input": dataset_item.get("input", {}), "output": [], "error": str(e)}


task = EvalTask(
    experiment_name="ToolSelectionExperiment",
    description="Evaluates the agent's ability to select the correct tools for a given command.",
    dataset_name="tool_selection_dataset",
    dataset_items=build_items(),
    task_fn=task_fn,
    metrics=[ToolSelectionQuality(), AgentPlanEfficiency(), tool_appropriateness_grader],
    # @TODO: improve how k is passed
    experiment_scoring_functions=[
        make_pass_at_k(k=1, metric_name=ToolSelectionQuality().name),
        make_pass_all_k(k=2, metric_name=ToolSelectionQuality().name),
    ],
)
