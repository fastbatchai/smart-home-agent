import json
import uuid

from datasets import memory_retrieval_dataset
from graders.deterministic import MemoryRetrievalCoverage, MemoryRetrievalQuality

from agent import extract_memory_context, run_agent
from src.memory import long_term_memory
from tasks.base import EvalTask


def seed_memories(user_id, memories):
    messages = [{"role": "user", "content": memory} for memory in memories]
    long_term_memory.add(messages=messages, user_id=user_id)


def cleanup_memories(user_id):
    long_term_memory.delete_all(user_id=user_id)


def build_items():
    return [
        {
            "input": value[0],
            "user_id": value[1],
            "home_template": value[2],
            "seeded_memories": json.dumps(value[3]),
            "expected_output": json.dumps(value[4]),
            "tags": value[5][0],
        }
        for value in memory_retrieval_dataset
    ]


def task_fn(dataset_item):
    try:
        command = dataset_item["input"]
        base_user_id = dataset_item["user_id"]
        home_template = dataset_item["home_template"]
        seeded_memories = json.loads(dataset_item["seeded_memories"])
        expected_keywords = json.loads(dataset_item["expected_output"])

        # Unique user_id per trial call — complete Mem0 isolation across Opik trials
        trial_user_id = f"{base_user_id}-{uuid.uuid4().hex[:6]}"
        seed_memories(trial_user_id, seeded_memories)
        # try:
        result = run_agent(home_template, command, user_id=trial_user_id)
        memory_context = extract_memory_context(result)

        return {
            "input": command,
            "output": memory_context,
            "expected_output": expected_keywords,
        }
    except Exception as e:
        return {"input": dataset_item.get("input", ""), "output": "", "error": str(e)}


task = EvalTask(
    experiment_name="MemoryRetrievalExperiment",
    description="Evaluates the agent's ability to retrieve and use long-term memory.",
    dataset_name="memory_retrieval_dataset",
    dataset_items=build_items(),
    task_fn=task_fn,
    metrics=[MemoryRetrievalQuality(), MemoryRetrievalCoverage()],
)
