from dataclasses import dataclass

from opik import Opik
from opik.evaluation import evaluate


@dataclass
class EvalTask:
    experiment_name: str
    description: str
    dataset_name: str
    dataset_items: list
    task_fn: callable
    metrics: list

    def run(self, client: Opik) -> None:
        dataset = client.get_or_create_dataset(self.dataset_name)
        dataset.insert(self.dataset_items)
        evaluate(
            experiment_name=self.experiment_name,
            dataset=dataset,
            task=self.task_fn,
            scoring_metrics=self.metrics,
        )
