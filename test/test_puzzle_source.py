import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evaluation.puzzle_source import generate_puzzle_buckets, _is_valid_puzzle_string

# 81-char string using only valid characters
_VALID = ("123456789" * 10)[:81]

# Test 1: valid 81-char puzzle string returns True
assert _is_valid_puzzle_string(_VALID), "Test 1 failed: valid 81-char string should pass"
assert _is_valid_puzzle_string("." * 81), "Test 1 failed: 81 dots should be valid"

# Test 2: wrong length returns False
assert not _is_valid_puzzle_string("1" * 80), "Test 2 failed: length 80 should be invalid"
assert not _is_valid_puzzle_string("1" * 82), "Test 2 failed: length 82 should be invalid"
assert not _is_valid_puzzle_string(""), "Test 2 failed: empty string should be invalid"

# Test 3: invalid characters return False
assert not _is_valid_puzzle_string("0" * 81), "Test 3 failed: '0' is not a valid character"
assert not _is_valid_puzzle_string("a" * 81), "Test 3 failed: letters are not valid"
assert not _is_valid_puzzle_string("1" * 80 + "X"), "Test 3 failed: 'X' is not a valid character"

# Generate buckets once for tests 4-8
buckets = generate_puzzle_buckets(2)

# Test 4: exactly four keys
expected_keys = {"easy", "medium", "hard", "expert"}
assert set(buckets.keys()) == expected_keys, (
    f"Test 4 failed: expected keys {expected_keys}, got {set(buckets.keys())}"
)

# Test 5: each bucket contains exactly 2 puzzles
for label, puzzles in buckets.items():
    assert len(puzzles) == 2, (
        f"Test 5 failed: bucket '{label}' has {len(puzzles)} puzzles, expected 2"
    )

# Test 6: every returned puzzle string passes validation
for label, puzzles in buckets.items():
    for i, puzzle in enumerate(puzzles):
        assert _is_valid_puzzle_string(puzzle), (
            f"Test 6 failed: bucket '{label}'[{i}] failed validation: {puzzle!r}"
        )

# Test 7: puzzles are plain str, not dokusan board objects
for label, puzzles in buckets.items():
    for i, puzzle in enumerate(puzzles):
        assert isinstance(puzzle, str), (
            f"Test 7 failed: bucket '{label}'[{i}] is {type(puzzle).__name__}, expected str"
        )

# Test 8: at least some diversity across the full result set
all_puzzles = [p for puzzles in buckets.values() for p in puzzles]
assert len(set(all_puzzles)) > 1, (
    "Test 8 failed: all returned puzzles are identical — no diversity"
)

print("All tests passed.")
