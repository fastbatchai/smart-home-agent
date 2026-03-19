"""Plot pass@k vs pass^k curves from Opik experiments.

Runs for all tasks and all metrics found in the data.
max_k is automatically set to the number of available trials.

Usage:
    # All tasks, all metrics
    python plot_pass_k.py --output-dir plots/

    # Single task
    python plot_pass_k.py --experiment DirectCommandsExperiment --output-dir plots/
"""

import argparse
import math
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import opik
from opik.exceptions import ExperimentNotFound
from pass_at_k import pass_at_k as _pass_at_k

from tasks import all_tasks


def fetch_all_scores(client: opik.Opik, experiment_name: str) -> dict[str, dict[str, list[float]]]:
    """Return {metric_name: {dataset_item_id: [score, ...]}} for all metrics in the experiment."""
    try:
        experiments = client.get_experiments_by_name(experiment_name)
    except ExperimentNotFound:
        return {}
    if not experiments:
        return {}

    groups: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for exp in experiments:
        for item in exp.get_items():
            for score in item.feedback_scores:
                groups[score["name"]][item.dataset_item_id].append(score["value"])

    return {metric: dict(items) for metric, items in groups.items()}


def pass_at_k(groups: dict, k: int, threshold: float) -> float:
    per_item = [
        _pass_at_k(
            num_total_samples_n=len(scores),
            num_correct_samples_c=sum(1 for s in scores if s >= threshold),
            k=k,
        )
        for scores in groups.values()
        if len(scores) >= k
    ]
    return sum(per_item) / len(per_item) if per_item else 0.0


def pass_all_k(groups: dict, k: int, threshold: float) -> float:
    per_item = []
    for scores in groups.values():
        n = len(scores)
        c = sum(1 for s in scores if s >= threshold)
        if n >= k:
            value = math.comb(c, k) / math.comb(n, k) if c >= k else 0.0
            per_item.append(value)
    return sum(per_item) / len(per_item) if per_item else 0.0


def plot(groups: dict, experiment_name: str, metric_name: str, threshold: float):
    n_trials = max(len(v) for v in groups.values())
    k_values = list(range(1, n_trials + 1))
    pass_at = [pass_at_k(groups, k, threshold) * 100 for k in k_values]
    pass_all = [pass_all_k(groups, k, threshold) * 100 for k in k_values]

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(k_values, pass_at, color="#4CAF50", linewidth=2.5, marker="o", markersize=7, label="pass@k  (>=1 success in k trials)")
    ax.plot(k_values, pass_all, color="#FF9800", linewidth=2.5, marker="o", markersize=7, label="pass^k  (all k trials succeed)")

    baseline = pass_at[0]
    ax.axhline(y=baseline, color="gray", linestyle="--", linewidth=1, alpha=0.6)
    ax.annotate(
        f"k=1 baseline: {baseline:.0f}%",
        xy=(max(k_values) * 0.55, baseline + 2),
        fontsize=10,
        color="gray",
    )

    ax.set_xlabel("Number of Trials (k)", fontsize=13)
    ax.set_ylabel("Success Rate (%)", fontsize=13)
    ax.set_title(f"Pass@k vs Pass^k\n{experiment_name}  -  {metric_name}", fontsize=14)
    ax.set_xlim(1, n_trials)
    ax.set_ylim(0, 108)
    ax.set_xticks(k_values)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11, loc="center right")

    plt.tight_layout()
    return fig


def main():
    parser = argparse.ArgumentParser(description="Plot pass@k vs pass^k for all tasks and metrics")
    parser.add_argument("--experiment", help="Filter to a single experiment name (default: all tasks)")
    parser.add_argument("--threshold", type=float, default=1.0, help="Score threshold for passing (default: 1.0)")
    parser.add_argument("--output-dir", default=".", help="Directory to save plots (default: current dir)")
    args = parser.parse_args()

    client = opik.Opik()
    os.makedirs(args.output_dir, exist_ok=True)

    tasks = [t for t in all_tasks if not args.experiment or t.experiment_name == args.experiment]
    if not tasks:
        print(f"No task found with experiment name: {args.experiment!r}")
        return

    for task in tasks:
        name = task.experiment_name
        print(f"\n{name}")
        all_scores = fetch_all_scores(client, name)

        if not all_scores:
            print(f"  No data found — skipping")
            continue

        for metric_name, groups in all_scores.items():
            n_trials = max(len(v) for v in groups.values())
            n_items = len(groups)
            print(f"  {metric_name}: {n_items} items, {n_trials} trials")

            fig = plot(groups, name, metric_name, args.threshold)
            safe_metric = metric_name.replace(":", "_").replace(" ", "_")
            filename = f"{name}__{safe_metric}.png"
            path = os.path.join(args.output_dir, filename)
            fig.savefig(path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            print(f"  Saved: {path}")


if __name__ == "__main__":
    main()
