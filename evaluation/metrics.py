from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field


_BUCKET_ORDER = ["easy", "medium", "hard", "expert"]


@dataclass
class BenchmarkResult:
    bucket: str
    puzzle: str
    solved: bool
    valid_solution: bool
    solve_time_seconds: float
    history_length: int
    final_num_fixed: int
    propagation_only: bool
    error: str = ""

    def to_row(self) -> dict[str, object]:
        return {
            "bucket": self.bucket,
            "puzzle": self.puzzle,
            "solved": self.solved,
            "valid_solution": self.valid_solution,
            "solve_time_seconds": self.solve_time_seconds,
            "history_length": self.history_length,
            "final_num_fixed": self.final_num_fixed,
            "propagation_only": self.propagation_only,
            "error": self.error,
        }


def summarize_results(results: list[BenchmarkResult]) -> list[dict[str, object]]:
    if not results:
        return []

    grouped: dict[str, list[BenchmarkResult]] = defaultdict(list)
    for r in results:
        grouped[r.bucket].append(r)

    known = [b for b in _BUCKET_ORDER if b in grouped]
    extra = sorted(b for b in grouped if b not in _BUCKET_ORDER)
    ordered_buckets = known + extra

    summary = []
    for bucket in ordered_buckets:
        bucket_results = grouped[bucket]
        total = len(bucket_results)
        solved_count = sum(1 for r in bucket_results if r.solved)
        times = [r.solve_time_seconds for r in bucket_results]
        prop_only_count = sum(1 for r in bucket_results if r.propagation_only)

        summary.append({
            "bucket": bucket,
            "total": total,
            "solved": solved_count,
            "success_rate": solved_count / total,
            "mean_time": statistics.mean(times),
            "median_time": statistics.median(times),
            "mean_iterations": statistics.mean(r.history_length for r in bucket_results),
            "propagation_only_count": prop_only_count,
            "propagation_only_rate": prop_only_count / total,
        })

    return summary
