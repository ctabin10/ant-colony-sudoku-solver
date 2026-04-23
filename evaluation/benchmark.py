"""Benchmark runner: orchestrates puzzle generation, solving, and result saving."""

from __future__ import annotations

import csv
import os
import sys
import time

# Ensure the project root is on sys.path when this file is run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aco.solver import SudokuACOSolver
from evaluation.metrics import BenchmarkResult, summarize_results
from evaluation.puzzle_source import generate_puzzle_buckets

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NUM_PER_BUCKET = 10
NUM_ANTS = 10
MAX_ITERATIONS = 200
Q0 = 0.9
XI = 0.1
RHO = 0.9
RHO_BVE = 0.005

RAW_RESULTS_PATH = "evaluation/results/raw_results.csv"
SUMMARY_RESULTS_PATH = "evaluation/results/summary.csv"


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def run_single_puzzle(bucket: str, puzzle: str) -> BenchmarkResult:
    solver = SudokuACOSolver(
        num_ants=NUM_ANTS,
        max_iterations=MAX_ITERATIONS,
        q0=Q0,
        xi=XI,
        rho=RHO,
        rho_bve=RHO_BVE,
    )

    start = time.perf_counter()
    try:
        board = solver.solve(puzzle)
        elapsed = time.perf_counter() - start

        return BenchmarkResult(
            bucket=bucket,
            puzzle=puzzle,
            solved=board.is_solved(),
            valid_solution=board.is_valid_solution(),
            solve_time_seconds=elapsed,
            history_length=len(solver.history),
            final_num_fixed=sum(1 for c in board.cells if c.is_fixed),
            propagation_only=(len(solver.history) == 0),
            error="",
        )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return BenchmarkResult(
            bucket=bucket,
            puzzle=puzzle,
            solved=False,
            valid_solution=False,
            solve_time_seconds=elapsed,
            history_length=0,
            final_num_fixed=0,
            propagation_only=False,
            error=str(exc),
        )


def save_raw_results(results: list[BenchmarkResult], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = [r.to_row() for r in results]
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def save_summary(results: list[BenchmarkResult], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rows = summarize_results(results)
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_benchmark(num_per_bucket: int = NUM_PER_BUCKET) -> list[BenchmarkResult]:
    buckets = generate_puzzle_buckets(num_per_bucket)
    results: list[BenchmarkResult] = []
    for bucket, puzzles in buckets.items():
        for puzzle in puzzles:
            results.append(run_single_puzzle(bucket, puzzle))
    return results


def print_summary(results: list[BenchmarkResult]) -> None:
    rows = summarize_results(results)
    print(f"\n{'Bucket':<10} {'Solved':>8} {'Rate':>8} {'Mean(s)':>10} {'Prop-only':>10}")
    print("-" * 52)
    for row in rows:
        print(
            f"{row['bucket']:<10} "
            f"{row['solved']}/{row['total']:>5} "
            f"{row['success_rate']:>7.1%} "
            f"{row['mean_time']:>10.3f} "
            f"{row['propagation_only_count']:>10}"
        )


def main() -> None:
    results = run_benchmark()
    save_raw_results(results, RAW_RESULTS_PATH)
    save_summary(results, SUMMARY_RESULTS_PATH)
    print_summary(results)


if __name__ == "__main__":
    main()
