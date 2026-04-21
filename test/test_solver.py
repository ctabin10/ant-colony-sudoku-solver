"""Tests for aco.solver.SudokuACOSolver — run with: python test/test_solver.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board
from sudoku.propagator import ConstraintPropagator
from aco.solver import SudokuACOSolver

# Easy puzzle — fully solved by propagation alone (verified in test_propagator)
PUZZLE = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

# Blank board — 81 empty cells, valid format, needs ACO search
BLANK = "." * 81

# Contradictory puzzle — digit '1' appears twice in row 0 (cells 0 and 1)
CONTRADICTION = "11" + "." * 79

# ------------------------------------------------------------------
# 1. Easy puzzle is solved by propagation; history is empty
# ------------------------------------------------------------------
solver1 = SudokuACOSolver()
result1 = solver1.solve(PUZZLE)
assert result1.is_solved(),         "easy puzzle must return a solved board"
assert len(solver1.history) == 0,   "propagation-only solution must not enter the loop"

# ------------------------------------------------------------------
# 2. Contradictory puzzle raises ValueError
# ------------------------------------------------------------------
try:
    SudokuACOSolver().solve(CONTRADICTION)
    assert False, "contradictory puzzle must raise ValueError"
except ValueError:
    pass

# ------------------------------------------------------------------
# 3. Wrong-length puzzle string raises ValueError (via Board.from_string)
# ------------------------------------------------------------------
try:
    SudokuACOSolver().solve("123")
    assert False, "short puzzle string must raise ValueError"
except ValueError:
    pass

# ------------------------------------------------------------------
# 4. history is cleared between consecutive calls
#    Insert a sentinel into history, then call solve() again and verify
#    the sentinel is gone.
# ------------------------------------------------------------------
solver4 = SudokuACOSolver(max_iterations=3)
solver4.solve(BLANK)
solver4.history.append((999, 0))   # sentinel — must be absent after next call
solver4.solve(BLANK)
assert (999, 0) not in solver4.history, \
    "history must be cleared at the start of every solve() call"
assert all(it <= 3 for it, _ in solver4.history), \
    "iteration indices must be within max_iterations"

# ------------------------------------------------------------------
# 5. solve() always returns a Board instance
# ------------------------------------------------------------------
assert isinstance(SudokuACOSolver().solve(PUZZLE), Board), \
    "solve() must return a Board"
assert isinstance(SudokuACOSolver(max_iterations=1).solve(BLANK), Board), \
    "solve() must return a Board even without a full solution"

# ------------------------------------------------------------------
# 6. max_iterations=0 returns the propagated base board unchanged
# ------------------------------------------------------------------
solver6 = SudokuACOSolver(max_iterations=0)
result6 = solver6.solve(BLANK)
assert isinstance(result6, Board),          "must return a Board"
assert len(solver6.history) == 0,           "no iterations means empty history"
assert all(len(c.domain) > 0 for c in result6.cells), \
    "returned board must have no empty domains"

# ------------------------------------------------------------------
# 7. is_valid_solution() and is_solved() direct tests
#    (these methods were added to board.py to support the solver)
# ------------------------------------------------------------------

# 7a. A fully propagated easy puzzle is solved and valid
b_solved = Board.from_string(PUZZLE)
ConstraintPropagator.initialize(b_solved)
assert b_solved.is_solved(),          "propagated easy puzzle must be solved"
assert b_solved.is_valid_solution(),  "propagated easy puzzle must be a valid solution"

# 7b. A blank board is neither solved nor a valid solution
b_blank = Board.from_string(BLANK)
assert not b_blank.is_solved(),         "blank board must not be solved"
assert not b_blank.is_valid_solution(), "blank board must not be a valid solution"

# 7c. is_valid_solution() catches a board with a duplicate in a unit
#     Manually place digit 5 in two cells of the same row
b_dup = Board.from_string(BLANK)
b_dup.cells[0].value = 5
b_dup.cells[1].value = 5   # duplicate 5 in row 0
assert not b_dup.is_valid_solution(), \
    "board with duplicate digit in a row must not be a valid solution"

print("All 7 test cases passed.")
