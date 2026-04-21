"""Tests for sudoku.propagator.ConstraintPropagator — run with: python test/test_propagator.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board
from sudoku.propagator import ConstraintPropagator

# Shared sample puzzle (same one used in test_board.py)
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

board = Board.from_string(PUZZLE)

# ------------------------------------------------------------------
# 1. initialize() returns True on a valid puzzle
# ------------------------------------------------------------------
result = ConstraintPropagator.initialize(board)
assert result is True, "initialize() should return True for a valid puzzle"

# ------------------------------------------------------------------
# 2. Givens remain fixed after initialization
#    PUZZLE[0] = '5'  → cell 0; PUZZLE[1] = '3' → cell 1
# ------------------------------------------------------------------
assert board.cells[0].domain == {5}, "given cell 0 must stay {5}"
assert board.cells[0].value == 5,    "given cell 0 value must be 5"
assert board.cells[1].domain == {3}, "given cell 1 must stay {3}"
assert board.cells[1].value == 3,    "given cell 1 value must be 3"

# ------------------------------------------------------------------
# 3. A peer of a given loses that digit from its domain
#    Cell 0 = digit 5; cell 4 is in the same row (row 0) → peer
# ------------------------------------------------------------------
assert 5 not in board.cells[4].domain, "peer (0,4) must not contain 5 after propagation"

# ------------------------------------------------------------------
# 4. No cell has an empty domain after initialization
# ------------------------------------------------------------------
for cell in board.cells:
    assert len(cell.domain) >= 1, f"cell {cell.index} has empty domain after initialization"

# ------------------------------------------------------------------
# 5. assign() on a valid unresolved cell collapses its domain
#    Use a fresh un-propagated board so we're guaranteed a non-fixed cell.
# ------------------------------------------------------------------
b5 = Board.from_string(PUZZLE)   # raw from_string; empty cells have {1..9}
target = next(c for c in b5.cells if not c.is_fixed)
chosen_digit = next(iter(target.domain))
ok = ConstraintPropagator.assign(b5, target.index, chosen_digit)
assert ok, "assign() on a legal cell/digit pair must return True"
assert b5.cells[target.index].domain == {chosen_digit}, \
    "domain must collapse to singleton after assign()"
assert b5.cells[target.index].value == chosen_digit, \
    "value must equal chosen digit after assign()"

# ------------------------------------------------------------------
# 6. assign() returns False when digit is not in the domain
#    Cell 0 has domain {5}; trying to assign 3 must fail
# ------------------------------------------------------------------
b6 = board.copy()
assert not ConstraintPropagator.assign(b6, 0, 3), \
    "assign() must return False for digit not in domain"

# ------------------------------------------------------------------
# 7. eliminate() returns False when the only remaining digit is removed
# ------------------------------------------------------------------
b7 = board.copy()
# Cell 0 has domain {5}; eliminating 5 empties the domain → contradiction
assert not ConstraintPropagator.eliminate(b7, 0, 5), \
    "eliminate() must return False when removing the sole remaining digit"

# ------------------------------------------------------------------
# 8. Propagation actually reduces at least some empty-cell domains
#    Cells that were '.' in the puzzle string must have reduced domains
#    (the easy puzzle is fully solved by propagation, so all are singletons)
# ------------------------------------------------------------------
originally_empty = [i for i, ch in enumerate(PUZZLE) if ch == "."]
reduced = [i for i in originally_empty if len(board.cells[i].domain) < 9]
assert len(reduced) > 0, \
    "at least one originally-empty cell must have a reduced domain after propagation"

# ------------------------------------------------------------------
# 9. Hidden-single (only-choice) test
#    Puzzle: box 0 has givens 1-8, leaving one empty cell that must be 9
#
#    Row 0: 1 2 3 . . . . . .
#    Row 1: 4 5 6 . . . . . .
#    Row 2: 7 8 . . . . . . .
#    Rows 3-8: all empty
#
#    Cell at index 20 (row 2, col 2) is the only empty cell in box 0.
#    After initialization it must be forced to 9 via Case D propagation.
# ------------------------------------------------------------------
FORCED_PUZZLE = (
    "123......"
    "456......"
    "78......."
    "........."
    "........."
    "........."
    "........."
    "........."
    "........."
)
b9 = Board.from_string(FORCED_PUZZLE)
ok9 = ConstraintPropagator.initialize(b9)
assert ok9, "initialize() must succeed on the forced puzzle"
assert b9.cells[20].domain == {9}, \
    "cell (2,2) must be forced to {9} by hidden-single propagation"
assert b9.cells[20].value == 9, \
    "cell (2,2) value must be 9 after propagation"

print("All 9 test cases passed.")
