import asyncio
import json

from datasets import tool_selection_dataset
from opik import Opik, track
from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result

from src.agent import create_agent_graph

client = Opik()

tool_selection_dataset_opik = client.get_or_create_dataset(
    name="tool_selection_dataset"
)

items = []
for value in tool_selection_dataset:
    item = {
        "input": (value[1], value[0]),
        "expected_output": json.dumps(value[2]),
        "forbidden_tools": json.dumps(value[3]),
        "tags": value[4][0],
    }
    items.append(item)

tool_selection_dataset_opik.insert(items)


@track
async def run_agent(
    home_template: str,
    command: str,
    user_name: str = "Alice",
    user_id: str = "alice-123",
    thread_id: str = "test-thread",
) -> dict:
    with open(f"./data/home_templates/{home_template}.json") as f:
        initial_home_state = json.load(f)["devices"]

    agent_graph = create_agent_graph().compile()

    state = {
        "messages": [command],
        "home_state": initial_home_state,
        "user_name": user_name,
        "user_id": user_id,
        "thread_id": thread_id,
    }
    configuration = {"configurable": {"user_id": user_id, "thread_id": thread_id}}

    return await agent_graph.ainvoke(state, config=configuration)


def extract_called_tools(result: dict) -> list[str]:
    called_tools = []
    for message in result["messages"]:
        # AIMessage with tool_calls
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                name = tc["name"] if isinstance(tc, dict) else tc.name
                called_tools.append(name)
    return called_tools


def evaluation_task(dataset_item):
    try:
        user_message_content = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected_tools = json.loads(dataset_item["expected_output"])
        forbidden_tools = json.loads(dataset_item.get("forbidden_tools", "[]"))

        result = asyncio.run(run_agent(home_template, user_message_content))
        called_tools = extract_called_tools(result)

        return {
            "input": user_message_content,
            "output": called_tools,
            "expected_output": expected_tools,
            "forbidden_tools": forbidden_tools,
        }

    except Exception as e:
        return {
            "input": dataset_item.get("input", {}),
            "output": [],
            "error": str(e),
        }


class ToolSelectionQuality(base_metric.BaseMetric):
    def __init__(self, name: str = "tool_selection_quality"):
        self.name = name

    def score(self, output, expected_output, forbidden_tools=None, **kwargs):
        try:
            # Check all expected tools were called (count-aware for repeated tools)
            remaining = list(output)
            missing = []
            for tool in expected_output:
                if tool in remaining:
                    remaining.remove(tool)
                else:
                    missing.append(tool)

            if missing:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason=f"Expected tools not called: {missing}. Called: {output}",
                )

            # Check no forbidden tools were called
            if forbidden_tools:
                called_forbidden = [t for t in forbidden_tools if t in output]
                if called_forbidden:
                    return score_result.ScoreResult(
                        name=self.name,
                        value=0,
                        reason=f"Forbidden tools were called: {called_forbidden}. Called: {output}",
                    )

            return score_result.ScoreResult(
                name=self.name,
                value=1,
                reason=f"All expected tools were called and no forbidden tools used: {output}",
            )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name, value=0, reason=f"Scoring error: {e}"
            )


def _is_subsequence_in_order(expected: list[str], actual: list[str]) -> bool:
    """Check that expected tools appear in actual in the correct relative order."""
    it = iter(actual)
    return all(tool in it for tool in expected)


class AgentPlanEfficiency(base_metric.BaseMetric):
    def __init__(self, name: str = "agent_plan_efficiency"):
        self.name = name

    def score(self, output, expected_output, **kwargs):
        try:
            optimal = len(expected_output)
            actual = len(output)

            if actual == 0:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason="Agent made no tool calls.",
                )

            # Check order: expected tools must appear in the correct relative order
            if not _is_subsequence_in_order(expected_output, output):
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason=f"Wrong tool call order. Expected sequence: {expected_output}. Got: {output}.",
                )

            if actual == optimal:
                return score_result.ScoreResult(
                    name=self.name,
                    value=1,
                    reason=f"Optimal plan: correct order and length ({actual} call(s)).",
                )

            # Correct order but extra calls — penalize proportionally
            efficiency = round(optimal / actual, 2)
            return score_result.ScoreResult(
                name=self.name,
                value=efficiency,
                reason=f"Correct order but too many calls: expected {optimal}, got {actual}. Efficiency: {efficiency}.",
            )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name, value=0, reason=f"Scoring error: {e}"
            )


metrics = [ToolSelectionQuality(), AgentPlanEfficiency()]

eval_results = evaluate(
    experiment_name="AgentToolSelectionExperiment",
    dataset=tool_selection_dataset_opik,
    task=evaluation_task,
    scoring_metrics=metrics,
)
