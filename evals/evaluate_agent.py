import asyncio
import json

from datasets import agent_completion_datasets
from langchain_core.messages import AIMessage
from opik import Opik, track
from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result

from src.agent import create_agent_graph

# os.environ["OPIK_API_KEY"] = "YOUR_API_KEY"
# os.environ["OPIK_WORKSPACE"] = "YOUR_WORKSPACE"

client = Opik()

agent_completion_dataset = client.get_or_create_dataset(name="agent_completion_dataset")

items = []
for dataset in agent_completion_datasets:
    for value in dataset:
        item = {
            "input": (value[1], value[0]),
            "expected_output": json.dumps(value[2]),
            "tags": value[3][0],
        }
        items.append(item)

agent_completion_dataset.insert(items)


@track
async def run_agent(
    home_template: str,
    command: str,
    user_name: str = "eval-user-01",
    user_id: str = "eval-user-01",
    thread_id: str = "eval-thread-01",
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


def get_last_ai_response(result: dict) -> str:
    """Return the content of the final AIMessage (non-tool-call) in the conversation."""
    for message in reversed(result["messages"]):
        if isinstance(message, AIMessage) and not getattr(message, "tool_calls", None):
            return message.content
    return ""


def evaluation_task(dataset_item):
    try:
        user_message_content = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected_home_state = json.loads(dataset_item["expected_output"])

        result = asyncio.run(run_agent(home_template, user_message_content))
        home_state = result["home_state"]
        agent_response = get_last_ai_response(result)

        return {
            "input": user_message_content,
            "output": agent_response,
            "expected_output": json.dumps(expected_home_state),
            "home_state": home_state,
        }

    except Exception as e:
        return {
            "input": dataset_item.get("input", {}),
            "output": "Error processing input.",
            "error": str(e),
        }


class AgentCompletionQuality(base_metric.BaseMetric):
    """Partial credit: ratio of expected device params set correctly."""

    def __init__(self, name: str = "agent_completion_quality"):
        self.name = name

    def score(self, output, expected_output, home_state=None, **kwargs):
        try:
            actual = home_state if home_state is not None else {}
            expected = (
                json.loads(expected_output)
                if isinstance(expected_output, str)
                else expected_output
            )

            total, correct, wrong = 0, 0, []
            for room, devices in expected.items():
                for device, params in devices.items():
                    for param, expected_value in params.items():
                        total += 1
                        try:
                            actual_value = actual[room][device][param]
                            if actual_value == expected_value:
                                correct += 1
                            else:
                                wrong.append(
                                    f"{room}.{device}.{param}: expected {expected_value}, got {actual_value}"
                                )
                        except KeyError:
                            wrong.append(f"{room}.{device}.{param}: missing in output")

            if total == 0:
                return score_result.ScoreResult(
                    name=self.name, value=0, reason="No expected params to check."
                )

            score_val = round(correct / total, 2)
            reason = (
                "All params correct."
                if not wrong
                else f"{correct}/{total} correct. Wrong: {wrong}"
            )
            return score_result.ScoreResult(
                name=self.name, value=score_val, reason=reason
            )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name, value=0, reason=f"Scoring error: {e}"
            )


metrics = [AgentCompletionQuality()]

# # This function runs the full evaluation process.
# # It loops over each dataset item and applies the `evaluation_task` function to generate outputs.
# # It then applies the custom `ToolSelectionQuality` metric (or any provided metrics) to score each result.
# # It logs the evaluation results to Opik under the specified experiment name ("AgentToolSelectionExperiment").
# # This allows tracking, comparing, and analyzing your agent's tool selection quality over time in Opik.

eval_results = evaluate(
    experiment_name="AgentCompletionExperiment",
    dataset=agent_completion_dataset,
    task=evaluation_task,
    scoring_metrics=metrics,
)
