import asyncio
import json

from datasets import memory_retrieval_dataset
from langchain_core.messages import ToolMessage
from opik import Opik, track
from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result

from src.agent import create_agent_graph
from src.memory import long_term_memory

client = Opik()

memory_retrieval_dataset_opik = client.get_or_create_dataset(
    name="memory_retrieval_dataset"
)

items = []
for value in memory_retrieval_dataset:
    item = {
        "input": value[0],  # command — shown as the test input in Opik
        "user_id": value[1],
        "home_template": value[2],
        "seeded_memories": json.dumps(value[3]),
        "expected_output": json.dumps(value[4]),
        "tags": value[5][0],
    }
    items.append(item)

memory_retrieval_dataset_opik.insert(items)


def seed_memories(user_id: str, memories: list[str]) -> None:
    """Add a list of memory strings to Mem0 for the given user."""
    for memory in memories:
        long_term_memory.add(
            messages=[{"role": "user", "content": memory}],
            user_id=user_id,
        )


def extract_memory_context(result: dict) -> str:
    """Collect all get_user_context ToolMessage contents from the agent result."""
    context_parts = []
    for message in result["messages"]:
        if isinstance(message, ToolMessage) and message.name == "get_user_context":
            context_parts.append(message.content)
    return "\n".join(context_parts)


@track
async def run_agent(
    home_template: str,
    command: str,
    user_id: str = "eval-user-01",
    user_name: str = "eval-user-01",
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
        command = dataset_item["input"]
        user_id = dataset_item["user_id"]
        home_template = dataset_item["home_template"]
        seeded_memories = json.loads(dataset_item["seeded_memories"])
        expected_keywords = json.loads(dataset_item["expected_output"])

        # Seed Mem0 with known facts for this test user before running the agent.
        # The agent will call get_user_context, which searches Mem0 and retrieves
        # these memories. We then check the retrieved context against expected_keywords.
        seed_memories(user_id, seeded_memories)

        result = asyncio.run(run_agent(home_template, command, user_id))
        retrieved_context = extract_memory_context(result)

        return {
            "input": command,
            "output": retrieved_context,
            "expected_output": expected_keywords,
        }

    except Exception as e:
        return {
            "input": dataset_item.get("input", ""),
            "output": "",
            "error": str(e),
        }


class MemoryRetrievalQuality(base_metric.BaseMetric):
    """Pass/fail: all expected keywords must appear in the retrieved memory context."""

    def __init__(self, name: str = "memory_retrieval_quality"):
        self.name = name

    def score(self, output, expected_output, **kwargs):
        try:
            if not output:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason="No memory context retrieved (get_user_context not called or returned empty).",
                )

            output_lower = output.lower()
            missing = [kw for kw in expected_output if kw.lower() not in output_lower]

            if missing:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason=f"Missing expected keywords: {missing}. Retrieved context: {output!r}",
                )

            return score_result.ScoreResult(
                name=self.name,
                value=1,
                reason=f"All expected keywords found in retrieved context: {expected_output}",
            )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name, value=0, reason=f"Scoring error: {e}"
            )


class MemoryRetrievalCoverage(base_metric.BaseMetric):
    """Partial credit: ratio of expected keywords found in the retrieved context."""

    def __init__(self, name: str = "memory_retrieval_coverage"):
        self.name = name

    def score(self, output, expected_output, **kwargs):
        try:
            if not output or not expected_output:
                return score_result.ScoreResult(
                    name=self.name,
                    value=0,
                    reason="No memory context retrieved or no expected keywords defined.",
                )

            output_lower = output.lower()
            found = [kw for kw in expected_output if kw.lower() in output_lower]
            coverage = round(len(found) / len(expected_output), 2)

            return score_result.ScoreResult(
                name=self.name,
                value=coverage,
                reason=f"Found {len(found)}/{len(expected_output)} expected keywords: {found}",
            )
        except Exception as e:
            return score_result.ScoreResult(
                name=self.name, value=0, reason=f"Scoring error: {e}"
            )


metrics = [MemoryRetrievalQuality(), MemoryRetrievalCoverage()]

eval_results = evaluate(
    experiment_name="MemoryRetrievalExperiment",
    dataset=memory_retrieval_dataset_opik,
    task=evaluation_task,
    scoring_metrics=metrics,
)
