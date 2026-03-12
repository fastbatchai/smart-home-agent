"""
Experiment-level pass@k metrics for Opik.

These are passed to evaluate() via experiment_scoring_functions.
Each function receives all TestResult objects after all trials complete
and returns a ScoreResult representing an aggregate metric.

A trial "passes" if the target metric score >= threshold (default 1.0).
"""

import math
from collections import defaultdict
from typing import List

from opik.evaluation.metrics.score_result import ScoreResult
from opik.evaluation.test_result import TestResult
from pass_at_k import pass_at_k as _pass_at_k


def _group_by_item(test_results: List[TestResult], metric_name: str) -> dict[str, list[float]]:
    """Group trial scores by dataset item. Returns {dataset_item_id: [score_trial_0, ...]}."""
    groups = defaultdict(list)
    for test_result in test_results:
        item_key = test_result.test_case.dataset_item_id
        for score_result in test_result.score_results:
            if score_result.name == metric_name:
                groups[item_key].append(score_result.value)
    return dict(groups)


def make_pass_at_k(k: int, metric_name: str, threshold: float = 1.0):
    """
    Returns an experiment-level scorer for pass@k.

    pass@k: probability of getting at least one correct solution in k attempts,
    estimated using the unbiased Chen et al. estimator, averaged across all dataset items.
    """
    def scorer(test_results: List[TestResult]) -> ScoreResult:
        groups = _group_by_item(test_results, metric_name)
        if not groups:
            return ScoreResult(name=f"pass@{k}", value=0.0)
        per_item = [
            _pass_at_k(
                num_total_samples_n=len(scores),
                num_correct_samples_c=sum(1 for s in scores if s >= threshold),
                k=k,
            )
            for scores in groups.values()
        ]
        return ScoreResult(name=f"pass@{k}", value=round(sum(per_item) / len(per_item), 3))

    return scorer


def make_pass_all_k(k: int, metric_name: str, threshold: float = 1.0):
    """
    Returns an experiment-level scorer for pass^k.

    pass^k: probability that ALL k attempts are correct, computed via the
    hypergeometric distribution C(c, k) / C(n, k), averaged across all dataset items.
    """
    def scorer(test_results: List[TestResult]) -> ScoreResult:
        groups = _group_by_item(test_results, metric_name)
        if not groups:
            return ScoreResult(name=f"pass^{k}", value=0.0)
        per_item = []
        for scores in groups.values():
            n = len(scores)
            c = sum(1 for s in scores if s >= threshold)
            value = math.comb(c, k) / math.comb(n, k) if n >= k and c >= k else 0.0
            per_item.append(value)
        return ScoreResult(name=f"pass^{k}", value=round(sum(per_item) / len(per_item), 3))

    return scorer
