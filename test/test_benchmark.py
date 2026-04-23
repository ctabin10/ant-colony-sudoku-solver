import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import csv
import evaluation.benchmark as bm
from evaluation.metrics import BenchmarkResult

_EASY_PUZZLE = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
_BLANK = "." * 81

_TEST_RAW_PATH = "evaluation/results/test_raw_results.csv"
_TEST_SUMMARY_PATH = "evaluation/results/test_summary.csv"


def _make_result(**kwargs) -> BenchmarkResult:
    defaults = dict(
        bucket="easy",
        puzzle=_BLANK,
        solved=True,
        valid_solution=True,
        solve_time_seconds=1.0,
        history_length=5,
        final_num_fixed=81,
        propagation_only=False,
        error="",
    )
    defaults.update(kwargs)
    return BenchmarkResult(**defaults)


# ---------------------------------------------------------------------------
# Test 1: run_single_puzzle returns a valid BenchmarkResult
# ---------------------------------------------------------------------------
result = bm.run_single_puzzle("easy", _EASY_PUZZLE)
assert result.bucket == "easy", f"Test 1 failed: bucket={result.bucket}"
assert result.puzzle == _EASY_PUZZLE, "Test 1 failed: puzzle mismatch"
assert result.solve_time_seconds >= 0, "Test 1 failed: negative solve time"
assert result.history_length >= 0, "Test 1 failed: negative history length"
assert result.final_num_fixed >= 0, "Test 1 failed: negative final_num_fixed"

# ---------------------------------------------------------------------------
# Test 2: run_single_puzzle handles solver exceptions via monkey-patch
# ---------------------------------------------------------------------------
class _BrokenSolver:
    def __init__(self, **_):
        self.history = []
    def solve(self, puzzle):
        raise RuntimeError("deliberate test failure")

_orig_solver = bm.SudokuACOSolver
bm.SudokuACOSolver = _BrokenSolver
err_result = bm.run_single_puzzle("hard", _BLANK)
bm.SudokuACOSolver = _orig_solver

assert err_result.solved is False, "Test 2 failed: solved should be False on exception"
assert err_result.valid_solution is False, "Test 2 failed: valid_solution should be False"
assert err_result.history_length == 0, "Test 2 failed: history_length should be 0"
assert err_result.final_num_fixed == 0, "Test 2 failed: final_num_fixed should be 0"
assert "deliberate test failure" in err_result.error, "Test 2 failed: error message missing"

# ---------------------------------------------------------------------------
# Test 3: save_raw_results writes a CSV with correct headers and row count
# ---------------------------------------------------------------------------
raw_results = [_make_result(bucket="easy"), _make_result(bucket="hard")]
bm.save_raw_results(raw_results, _TEST_RAW_PATH)
assert os.path.exists(_TEST_RAW_PATH), "Test 3 failed: CSV not created"
with open(_TEST_RAW_PATH, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
expected_headers = {
    "bucket", "puzzle", "solved", "valid_solution", "solve_time_seconds",
    "history_length", "final_num_fixed", "propagation_only", "error",
}
assert set(reader.fieldnames) == expected_headers, f"Test 3 failed: headers={reader.fieldnames}"
assert len(rows) == 2, f"Test 3 failed: expected 2 rows, got {len(rows)}"

# ---------------------------------------------------------------------------
# Test 4: save_summary writes a CSV with correct headers and row count
# ---------------------------------------------------------------------------
summary_results = [_make_result(bucket="easy"), _make_result(bucket="medium")]
bm.save_summary(summary_results, _TEST_SUMMARY_PATH)
assert os.path.exists(_TEST_SUMMARY_PATH), "Test 4 failed: summary CSV not created"
with open(_TEST_SUMMARY_PATH, newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
expected_summary_headers = {
    "bucket", "total", "solved", "success_rate", "mean_time", "median_time",
    "mean_iterations", "propagation_only_count", "propagation_only_rate",
}
assert set(reader.fieldnames) == expected_summary_headers, f"Test 4 failed: headers={reader.fieldnames}"
assert len(rows) == 2, f"Test 4 failed: expected 2 rows, got {len(rows)}"

# ---------------------------------------------------------------------------
# Test 5: run_benchmark uses puzzle buckets correctly (monkey-patched)
# ---------------------------------------------------------------------------
_fake_buckets = {
    "easy": [_BLANK, _BLANK],
    "medium": [_BLANK],
}
_fake_result = _make_result()

_orig_gpb = bm.generate_puzzle_buckets
_orig_rsp = bm.run_single_puzzle

bm.generate_puzzle_buckets = lambda n: _fake_buckets
bm.run_single_puzzle = lambda bucket, puzzle: _make_result(bucket=bucket, puzzle=puzzle)

bench_results = bm.run_benchmark(num_per_bucket=2)

bm.generate_puzzle_buckets = _orig_gpb
bm.run_single_puzzle = _orig_rsp

assert len(bench_results) == 3, f"Test 5 failed: expected 3 results, got {len(bench_results)}"
buckets_seen = [r.bucket for r in bench_results]
assert buckets_seen.count("easy") == 2, "Test 5 failed: expected 2 easy results"
assert buckets_seen.count("medium") == 1, "Test 5 failed: expected 1 medium result"

# ---------------------------------------------------------------------------
# Test 6: print_summary does not crash on a small result set
# ---------------------------------------------------------------------------
small_results = [
    _make_result(bucket="easy", solved=True),
    _make_result(bucket="hard", solved=False),
]
bm.print_summary(small_results)  # must not raise

# ---------------------------------------------------------------------------
# Test 7: main() runs end-to-end with lightweight monkey-patches
# ---------------------------------------------------------------------------
_fake_main_results = [_make_result(bucket="easy")]

_orig_run = bm.run_benchmark
_orig_save_raw = bm.save_raw_results
_orig_save_sum = bm.save_summary
_orig_print = bm.print_summary

bm.run_benchmark = lambda: _fake_main_results
bm.save_raw_results = lambda results, path: None
bm.save_summary = lambda results, path: None
bm.print_summary = lambda results: None

bm.main()

bm.run_benchmark = _orig_run
bm.save_raw_results = _orig_save_raw
bm.save_summary = _orig_save_sum
bm.print_summary = _orig_print

print("All tests passed.")
