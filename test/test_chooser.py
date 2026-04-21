"""Tests for aco.chooser.ValueChooser — run with: python test/test_chooser.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board
from aco.pheromone import PheromoneMatrix
from aco.chooser import ValueChooser


# ------------------------------------------------------------------
# RNG stubs for deterministic tests
# ------------------------------------------------------------------

class FixedRng:
    """Always returns the same float from random()."""
    def __init__(self, value: float):
        self._value = value
    def random(self) -> float:
        return self._value
    def choice(self, seq):
        return seq[0]


class SequenceRng:
    """Returns successive floats from a list, then repeats the last."""
    def __init__(self, values: list):
        self._values = values
        self._idx = 0
    def random(self) -> float:
        v = self._values[self._idx]
        self._idx = min(self._idx + 1, len(self._values) - 1)
        return v
    def choice(self, seq):
        return seq[0]


# Shared board — all cells start as empty (domain {1..9})
BLANK = "." * 81
board = Board.from_string(BLANK)

# ------------------------------------------------------------------
# 1. Singleton domain: choose() returns that digit without sampling
# ------------------------------------------------------------------
board.cells[0].domain = {5}
board.cells[0].value = 5
pm1 = PheromoneMatrix()
chooser1 = ValueChooser(pheromone=pm1, rng=FixedRng(0.99))  # q always >= q0
assert ValueChooser(pheromone=pm1, rng=FixedRng(0.99)).choose(board, 0) == 5, \
    "singleton domain must return that digit directly"

# Restore cell 0 for later tests
board.cells[0].domain = set(range(1, 10))
board.cells[0].value = 0

# ------------------------------------------------------------------
# 2. Empty domain: choose() raises ValueError
# ------------------------------------------------------------------
board.cells[1].domain = set()
try:
    ValueChooser(pheromone=PheromoneMatrix()).choose(board, 1)
    assert False, "empty domain should raise ValueError"
except ValueError:
    pass
board.cells[1].domain = set(range(1, 10))  # restore

# ------------------------------------------------------------------
# 3. Greedy choice picks the highest-pheromone legal digit
#    domain={2,4,7}, tau(2)=0.5, tau(4)=0.3, tau(7)=0.2
#    q=0.1 < q0=0.9  →  greedy  →  must pick 2
# ------------------------------------------------------------------
pm3 = PheromoneMatrix()
pm3.set(2, 2, 0.5)
pm3.set(2, 4, 0.3)
pm3.set(2, 7, 0.2)
board.cells[2].domain = {2, 4, 7}
board.cells[2].value = 0
result3 = ValueChooser(pheromone=pm3, q0=0.9, rng=FixedRng(0.1)).choose(board, 2)
assert result3 == 2, f"greedy must pick digit 2 (highest tau), got {result3}"

# ------------------------------------------------------------------
# 4. Greedy ignores illegal digits even with huge pheromone
#    domain={4,7}, tau(2)=100.0 but 2 is NOT in domain
#    greedy must pick 4 (highest tau among legal)
# ------------------------------------------------------------------
pm4 = PheromoneMatrix()
pm4.set(3, 2, 100.0)   # illegal — not in domain
pm4.set(3, 4, 0.3)
pm4.set(3, 7, 0.2)
board.cells[3].domain = {4, 7}
board.cells[3].value = 0
result4 = ValueChooser(pheromone=pm4, q0=0.9, rng=FixedRng(0.1)).choose(board, 3)
assert result4 == 4, f"greedy must ignore digit 2 (illegal), got {result4}"

# ------------------------------------------------------------------
# 5. Roulette choice uses only legal digits
#    domain={2,4,7}, weights=[0.5, 0.3, 0.2], total=1.0
#    q0=0.0  →  roulette always
#    RNG sequence: q=0.5 (triggers roulette), roulette_r=0.6
#    cumulative: 0.5(2), 0.8(4), 1.0(7)  →  0.6 lands in [0.5,0.8)  →  digit 4
# ------------------------------------------------------------------
pm5 = PheromoneMatrix()
pm5.set(4, 2, 0.5)
pm5.set(4, 4, 0.3)
pm5.set(4, 7, 0.2)
board.cells[4].domain = {2, 4, 7}
board.cells[4].value = 0
result5 = ValueChooser(
    pheromone=pm5, q0=0.0,
    rng=SequenceRng([0.5, 0.6])   # q=0.5 → roulette; r=0.6 → digit 4
).choose(board, 4)
assert result5 == 4, f"roulette must pick digit 4 at r=0.6, got {result5}"

# ------------------------------------------------------------------
# 6. Roulette falls back to uniform random when all weights are zero
#    Stub choice() returns seq[0] = smallest sorted digit = 2
# ------------------------------------------------------------------
pm6 = PheromoneMatrix()
for d in range(1, 10):
    pm6.set(5, d, 0.0)
board.cells[5].domain = {2, 4, 7}
board.cells[5].value = 0
# q=0.5 >= q0=0.0 → roulette; total=0 → fallback; choice returns seq[0]=2
result6 = ValueChooser(
    pheromone=pm6, q0=0.0,
    rng=SequenceRng([0.5])
).choose(board, 5)
assert result6 == 2, f"zero-weight fallback must return seq[0]=2, got {result6}"

# ------------------------------------------------------------------
# 7. Greedy tie-breaking is deterministic (smallest sorted digit)
#    domain={4,7}, both have tau=tau0 (equal pheromone)
#    greedy must return 4 (first in sorted order)
# ------------------------------------------------------------------
pm7 = PheromoneMatrix(tau0=0.5)   # all entries equal 0.5
board.cells[6].domain = {4, 7}
board.cells[6].value = 0
result7 = ValueChooser(pheromone=pm7, q0=0.9, rng=FixedRng(0.1)).choose(board, 6)
assert result7 == 4, f"tie-breaking must return smallest digit (4), got {result7}"

# ------------------------------------------------------------------
# 8. choose() does not mutate the board or cell domain
# ------------------------------------------------------------------
board.cells[7].domain = {3, 6, 9}
board.cells[7].value = 0
original_domain = frozenset(board.cells[7].domain)
pm8 = PheromoneMatrix()
ValueChooser(pheromone=pm8, q0=0.9, rng=FixedRng(0.1)).choose(board, 7)
assert frozenset(board.cells[7].domain) == original_domain, \
    "choose() must not mutate cell domain"
assert board.cells[7].value == 0, \
    "choose() must not mutate cell value"

print("All 8 test cases passed.")
