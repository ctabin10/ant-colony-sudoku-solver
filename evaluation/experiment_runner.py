"""Baseline experiment runner: repeats the benchmark multiple times and averages results."""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collections import defaultdict

from evaluation.benchmark import run_benchmark
from evaluation.metrics import summarize_results

# ---------------------------------------------------------------------------
# Baseline configuration
# ---------------------------------------------------------------------------

NUM_RUNS = 10
NUM_PER_BUCKET = 100
NUM_ANTS = 5
MAX_ITERATIONS = 20

BASELINE_CSV_PATH = "evaluation/results/baseline_results.csv"

_BUCKET_ORDER = ["easy", "medium", "hard", "expert"]


# ---------------------------------------------------------------------------
# Experiment logic
# ---------------------------------------------------------------------------

def run_experiment(
    num_runs: int = NUM_RUNS,
    num_per_bucket: int = NUM_PER_BUCKET,
    num_ants: int = NUM_ANTS,
    max_iterations: int = MAX_ITERATIONS,
) -> list[dict]:
    """Run the benchmark `num_runs` times and return per-run summary rows."""
    all_summary_rows: list[dict] = []

    for run_idx in range(num_runs):
        print(f"  Run {run_idx + 1}/{num_runs}...", flush=True)
        results = run_benchmark(
            num_per_bucket=num_per_bucket,
            num_ants=num_ants,
            max_iterations=max_iterations,
        )
        for row in summarize_results(results):
            all_summary_rows.append({"run": run_idx + 1, **row})

    return all_summary_rows


def compute_averages(summary_rows: list[dict]) -> list[dict]:
    """Average per-bucket stats across all runs, plus an overall row."""
    accum: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))

    for row in summary_rows:
        b = row["bucket"]
        accum[b]["success_rate"].append(row["success_rate"])
        accum[b]["mean_time"].append(row["mean_time"])
        accum[b]["propagation_only_count"].append(row["propagation_only_count"])

    known = [b for b in _BUCKET_ORDER if b in accum]
    extra = sorted(b for b in accum if b not in _BUCKET_ORDER)

    avg_rows: list[dict] = []
    all_rates, all_times, all_prop = [], [], []

    for bucket in known + extra:
        rates = accum[bucket]["success_rate"]
        times = accum[bucket]["mean_time"]
        props = accum[bucket]["propagation_only_count"]
        avg_rows.append({
            "bucket": bucket,
            "avg_solved_rate": sum(rates) / len(rates),
            "avg_mean_time_s": sum(times) / len(times),
            "avg_prop_only_count": sum(props) / len(props),
        })
        all_rates.extend(rates)
        all_times.extend(times)
        all_prop.extend(props)

    avg_rows.append({
        "bucket": "overall",
        "avg_solved_rate": sum(all_rates) / len(all_rates),
        "avg_mean_time_s": sum(all_times) / len(all_times),
        "avg_prop_only_count": sum(all_prop) / len(all_prop),
    })

    return avg_rows


def save_baseline_csv(summary_rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not summary_rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)


def print_experiment_summary(
    avg_rows: list[dict],
    num_runs: int,
    num_per_bucket: int,
    num_ants: int,
    max_iterations: int,
) -> None:
    total_attempts = num_runs * num_per_bucket * len(_BUCKET_ORDER)
    print(f"\nBaseline Experiment")
    print(f"  NUM_RUNS         = {num_runs}")
    print(f"  NUM_PER_BUCKET   = {num_per_bucket}")
    print(f"  NUM_ANTS         = {num_ants}")
    print(f"  MAX_ITERATIONS   = {max_iterations}")
    print(f"  TOTAL_ATTEMPTS   = {total_attempts}")
    print()
    print(f"{'Bucket':<10} {'Avg Solved Rate':>16} {'Avg Mean Time(s)':>17} {'Avg Prop-only':>14}")
    print("-" * 62)
    for row in avg_rows:
        print(
            f"{row['bucket']:<10} "
            f"{row['avg_solved_rate']:>15.1%} "
            f"{row['avg_mean_time_s']:>17.4f} "
            f"{row['avg_prop_only_count']:>14.1f}"
        )


def main() -> None:
    print(f"Running baseline experiment ({NUM_RUNS} runs × {NUM_PER_BUCKET} puzzles × 4 buckets)...")
    summary_rows = run_experiment()
    avg_rows = compute_averages(summary_rows)
    save_baseline_csv(summary_rows, BASELINE_CSV_PATH)
    print_experiment_summary(avg_rows, NUM_RUNS, NUM_PER_BUCKET, NUM_ANTS, MAX_ITERATIONS)
    print(f"\nRaw per-run data saved to: {BASELINE_CSV_PATH}")


if __name__ == "__main__":
    main()
