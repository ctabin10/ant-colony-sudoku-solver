"""Tests for aco.ant.Ant and aco.ant_solver.AntSolver — run with: python test/test_ant.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board
from aco.ant import Ant
from aco.ant_solver import AntSolver
from aco.pheromone import PheromoneMatrix
from aco.chooser import ValueChooser


# ------------------------------------------------------------------
# Stub chooser — always returns the same digit regardless of domain
# ------------------------------------------------------------------
class StubChooser:
    def __init__(self, digit: int):
        self._digit = digit
    def choose(self, board, cell_index: int) -> int:
        return self._digit


BLANK = "." * 81

# ------------------------------------------------------------------
# 1. Ant initialises with correct defaults
# ------------------------------------------------------------------
board1 = Board.from_string(BLANK)
ant1 = Ant(board=board1, start_index=3, current_index=3)
assert ant1.path == [],         "path must start empty"
assert ant1.failed is False,    "failed must start False"
assert ant1.num_fixed == 0,     "num_fixed must start 0"
assert ant1.start_index == 3,   "start_index must be preserved"
assert ant1.current_index == 3, "current_index must be preserved"

# ------------------------------------------------------------------
# 2. step() skips an already-fixed cell and advances index
# ------------------------------------------------------------------
board2 = Board.from_string(BLANK)
board2.cells[5].domain = {7}
board2.cells[5].value = 7
ant2 = Ant(board=board2, start_index=5, current_index=5)
AntSolver.step(ant2, StubChooser(1), PheromoneMatrix())
assert ant2.current_index == 6, "index must advance past a fixed cell"
assert ant2.path == [],         "path must remain empty for a skipped cell"
assert not ant2.failed,         "ant must not fail on a fixed cell"

# ------------------------------------------------------------------
# 3. step() marks ant failed when current cell has empty domain
# ------------------------------------------------------------------
board3 = Board.from_string(BLANK)
board3.cells[0].domain = set()
ant3 = Ant(board=board3, start_index=0, current_index=0)
AntSolver.step(ant3, StubChooser(1), PheromoneMatrix())
assert ant3.failed,             "ant must fail on empty domain"
assert ant3.path == [],         "path must be empty after failure"

# ------------------------------------------------------------------
# 4. Successful unresolved-cell step: path updated, pheromone updated,
#    index advances
# ------------------------------------------------------------------
board4 = Board.from_string(BLANK)
pm4 = PheromoneMatrix()
tau_before = pm4.get(0, 5)
ant4 = Ant(board=board4, start_index=0, current_index=0)
AntSolver.step(ant4, StubChooser(5), pm4)
assert ant4.path == [(0, 5)],   "path must record (cell_index, digit)"
assert pm4.get(0, 5) != tau_before, "pheromone must be updated after assignment"
assert ant4.current_index == 1, "index must advance after successful step"
assert not ant4.failed,         "ant must not be failed after successful step"

# ------------------------------------------------------------------
# 5. step() marks ant failed when assign() fails
#    domain={1,2,3}, stub returns 9 (not in domain) → assign returns False
# ------------------------------------------------------------------
board5 = Board.from_string(BLANK)
board5.cells[0].domain = {1, 2, 3}
board5.cells[0].value = 0
ant5 = Ant(board=board5, start_index=0, current_index=0)
AntSolver.step(ant5, StubChooser(9), PheromoneMatrix())
assert ant5.failed,             "ant must fail when assign() fails"
assert ant5.path == [],         "path must not be updated on failed assignment"

# ------------------------------------------------------------------
# 6. run_ant() sets num_fixed to the correct count after the run
# ------------------------------------------------------------------
import random
board6 = Board.from_string(BLANK)
pm6 = PheromoneMatrix()
chooser6 = ValueChooser(pheromone=pm6, rng=random.Random(0))
ant6 = Ant(board=board6, start_index=0, current_index=0)
AntSolver.run_ant(ant6, chooser6, pm6)
expected_fixed = sum(1 for c in ant6.board.cells if len(c.domain) == 1)
assert ant6.num_fixed == expected_fixed, \
    f"num_fixed {ant6.num_fixed} must match actual fixed count {expected_fixed}"

# ------------------------------------------------------------------
# 7. Index wraparound: current_index=80 advances to 0
# ------------------------------------------------------------------
board7 = Board.from_string(BLANK)
board7.cells[80].domain = {9}
board7.cells[80].value = 9
ant7 = Ant(board=board7, start_index=80, current_index=80)
AntSolver.step(ant7, StubChooser(1), PheromoneMatrix())
assert ant7.current_index == 0, "index must wrap from 80 to 0"

# ------------------------------------------------------------------
# 8. Propagated consequences are NOT added to path
#    Setup:
#      cell 0: domain {5, 9}
#      cell 1: domain {5, 7}  ← peer of cell 0 (same row/box)
#    Stub chooses 5 for cell 0.
#    After assign: cell 0 → {5}, cell 1 forced → {7} by propagation.
#    path must contain only (0, 5), not (1, 7).
# ------------------------------------------------------------------
board8 = Board.from_string(BLANK)
board8.cells[0].domain = {5, 9}
board8.cells[0].value = 0
board8.cells[1].domain = {5, 7}
board8.cells[1].value = 0
ant8 = Ant(board=board8, start_index=0, current_index=0)
AntSolver.step(ant8, StubChooser(5), PheromoneMatrix())
assert not ant8.failed,              "ant must not fail on this assignment"
assert ant8.path == [(0, 5)],        "only the explicit choice must be in path"
assert board8.cells[1].domain == {7}, "cell 1 must be forced to {7} by propagation"
assert (1, 7) not in ant8.path,      "propagated cell 1 must NOT appear in path"

print("All 8 test cases passed.")
