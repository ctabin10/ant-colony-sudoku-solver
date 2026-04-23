import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.metrics import BenchmarkResult, summarize_results

_PUZZLE = "." * 81


def make_result(**kwargs) -> BenchmarkResult:
    defaults = dict(
        bucket="easy",
        puzzle=_PUZZLE,
        solved=True,
        valid_solution=True,
        solve_time_seconds=1.0,
        history_length=10,
        final_num_fixed=81,
        propagation_only=False,
        error="",
    )
    defaults.update(kwargs)
    return BenchmarkResult(**defaults)


# Test 1: fields stored correctly
r = make_result(bucket="hard", solved=False, solve_time_seconds=3.5, history_length=42)
assert r.bucket == "hard"
assert r.solved is False
assert r.solve_time_seconds == 3.5
assert r.history_length == 42
assert r.error == ""

# Test 2: to_row() returns correct keys and values
r = make_result(bucket="easy", solved=True, propagation_only=True, error="oops")
row = r.to_row()
expected_keys = {
    "bucket", "puzzle", "solved", "valid_solution", "solve_time_seconds",
    "history_length", "final_num_fixed", "propagation_only", "error",
}
assert set(row.keys()) == expected_keys, f"Test 2 failed: unexpected keys {set(row.keys())}"
assert row["bucket"] == "easy"
assert row["solved"] is True
assert row["propagation_only"] is True
assert row["error"] == "oops"

# Test 3: empty input returns []
assert summarize_results([]) == [], "Test 3 failed: expected []"

# Test 4: single-result bucket
r = make_result(bucket="medium", solved=True, solve_time_seconds=2.0,
                history_length=5, propagation_only=True)
summary = summarize_results([r])
assert len(summary) == 1
s = summary[0]
assert s["bucket"] == "medium"
assert s["total"] == 1
assert s["solved"] == 1
assert s["success_rate"] == 1.0
assert s["mean_time"] == 2.0
assert s["median_time"] == 2.0
assert s["mean_iterations"] == 5.0
assert s["propagation_only_count"] == 1
assert s["propagation_only_rate"] == 1.0

# Test 5: multiple results in one bucket, hand-verifiable
results = [
    make_result(bucket="hard", solved=True,  solve_time_seconds=2.0, history_length=10, propagation_only=False),
    make_result(bucket="hard", solved=True,  solve_time_seconds=4.0, history_length=20, propagation_only=True),
    make_result(bucket="hard", solved=False, solve_time_seconds=6.0, history_length=30, propagation_only=False),
]
summary = summarize_results(results)
assert len(summary) == 1
s = summary[0]
assert s["total"] == 3
assert s["solved"] == 2
assert abs(s["success_rate"] - 2/3) < 1e-9
assert abs(s["mean_time"] - 4.0) < 1e-9       # (2+4+6)/3
assert s["median_time"] == 4.0
assert abs(s["mean_iterations"] - 20.0) < 1e-9  # (10+20+30)/3
assert s["propagation_only_count"] == 1
assert abs(s["propagation_only_rate"] - 1/3) < 1e-9

# Test 6: multiple buckets appear in the required order
results = [
    make_result(bucket="expert"),
    make_result(bucket="easy"),
    make_result(bucket="hard"),
    make_result(bucket="medium"),
]
summary = summarize_results(results)
assert [s["bucket"] for s in summary] == ["easy", "medium", "hard", "expert"], (
    f"Test 6 failed: got order {[s['bucket'] for s in summary]}"
)

# Test 7: unknown bucket names appear after the four standard ones, sorted alphabetically
results = [
    make_result(bucket="expert"),
    make_result(bucket="diabolical"),
    make_result(bucket="easy"),
    make_result(bucket="beginner"),
]
summary = summarize_results(results)
buckets = [s["bucket"] for s in summary]
assert buckets == ["easy", "expert", "beginner", "diabolical"], (
    f"Test 7 failed: got order {buckets}"
)

# Test 8: success_rate and propagation_only_rate are floats in [0, 1]
results = [
    make_result(bucket="easy", solved=True,  propagation_only=True),
    make_result(bucket="easy", solved=False, propagation_only=False),
]
summary = summarize_results(results)
s = summary[0]
assert isinstance(s["success_rate"], float), "Test 8 failed: success_rate not float"
assert isinstance(s["propagation_only_rate"], float), "Test 8 failed: propagation_only_rate not float"
assert 0.0 <= s["success_rate"] <= 1.0
assert 0.0 <= s["propagation_only_rate"] <= 1.0

# Test 9: error field does not break summarization
results = [
    make_result(bucket="easy", solved=False, error="timeout"),
    make_result(bucket="easy", solved=True,  error=""),
]
summary = summarize_results(results)
assert len(summary) == 1
assert summary[0]["total"] == 2
assert summary[0]["solved"] == 1

print("All tests passed.")
