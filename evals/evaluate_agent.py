import asyncio
import json

from datasets import agent_completion_datasets
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


def evaluation_task(dataset_item):
    try:
        user_message_content = dataset_item["input"][0]
        home_template = dataset_item["input"][1]
        expected_home_state = json.loads(dataset_item["expected_output"])

        # This is where you call your agent with the input message and get the real execution results.
        result = asyncio.run(run_agent(home_template, user_message_content))
        home_state = result["home_state"]
        return {
            "input": user_message_content,
            "output": home_state,
            "expected_output": expected_home_state,
        }

    except Exception as e:
        return {
            "input": dataset_item.get("input", {}),
            "output": "Error processing input.",
            "error": str(e),
        }


class AgentCompletionQuality(base_metric.BaseMetric):
    def __init__(self, name: str = "agent_completion_quality"):
        self.name = name

    def score(self, output, expected_output, **kwargs):
        try:
            for room, devices in expected_output.items():
                for device, params in devices.items():
                    for param, expected_value in params.items():
                        if output[room][device][param] != expected_value:
                            return score_result.ScoreResult(
                                name=self.name,
                                value=0,
                                reason=f"Wrong value. Expected {expected_value} for {room}.{device}.{param}, got {output[room][device][param]}",
                            )

            return score_result.ScoreResult(
                name=self.name,
                value=1,
                reason="The agent completed the task correctly",
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
