from dataclasses import dataclass

from opik import Opik
from opik.evaluation import evaluate

from src.config import config
from src.prompts import AGENT_SYSTEM_PROMPT


def _experiment_config() -> dict:
    provider = config.LLM_PROVIDER.lower()
    model = {
        "groq": config.GROQ_LLM_MODEL,
        "openai": config.OPENAI_MODEL_NAME,
        "ollama": config.OLLAMA_MODEL_NAME,
    }.get(provider, "unknown")
    return {
        "llm_provider": provider,
        "model": model,
        "skip_memory": config.SKIP_MEMORY,
        "test_mode": config.TEST_MODE,
        "agent_prompt": AGENT_SYSTEM_PROMPT,
    }


@dataclass
class EvalTask:
    experiment_name: str
    description: str
    dataset_name: str
    dataset_items: list
    task_fn: callable
    metrics: list

    def run(self, client: Opik, n_trials: int = 1) -> None:
        dataset = client.get_or_create_dataset(self.dataset_name)
        dataset.insert(self.dataset_items)
        experiment_config = _experiment_config()
        experiment_config["n_trials"] = n_trials
        evaluate(
            experiment_name=self.experiment_name,
            dataset=dataset,
            task=self.task_fn,
            scoring_metrics=self.metrics,
            trial_count=n_trials,
            experiment_config=experiment_config,
        )
