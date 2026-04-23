"""
Puzzle sourcing layer for the evaluation pipeline.

Uses dokusan to generate Sudoku puzzles grouped by difficulty label.
dokusan's avg_rank parameter maps to difficulty as follows:
  easy   -> avg_rank=30  (~32 empty cells)
  medium -> avg_rank=50  (~40 empty cells)
  hard   -> avg_rank=100 (~53 empty cells)
  expert -> avg_rank=200 (~55 empty cells, harder constraints)
"""

from dokusan import generators


_DIFFICULTY_RANKS: dict[str, int] = {
    "easy": 30,
    "medium": 50,
    "hard": 100,
    "expert": 200,
}


def _is_valid_puzzle_string(puzzle: str) -> bool:
    if len(puzzle) != 81:
        return False
    return all(ch in "123456789." for ch in puzzle)


def generate_puzzle_buckets(num_per_bucket: int) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {label: [] for label in _DIFFICULTY_RANKS}

    for label, rank in _DIFFICULTY_RANKS.items():
        while len(buckets[label]) < num_per_bucket:
            raw = str(generators.random_sudoku(avg_rank=rank))
            normalized = raw.replace("0", ".")
            if _is_valid_puzzle_string(normalized):
                buckets[label].append(normalized)

    return buckets
