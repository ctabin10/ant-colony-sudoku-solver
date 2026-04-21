"""Tests for sudoku.board.Board — run with: python test/test_board.py"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board

# A well-known easy puzzle (81 chars, '.' = empty)
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
# 1. Exactly 81 cells
# ------------------------------------------------------------------
assert len(board.cells) == 81, "board must have 81 cells"

# ------------------------------------------------------------------
# 2. Every cell has exactly 20 peers
# ------------------------------------------------------------------
for cell in board.cells:
    assert len(cell.peers) == 20, (
        f"cell {cell.index} has {len(cell.peers)} peers, expected 20"
    )

# ------------------------------------------------------------------
# 3. Row / col / box assignments for a few known cells
# ------------------------------------------------------------------
# cell at index 0 → row 0, col 0, box 0
c0 = board.cells[0]
assert c0.row == 0 and c0.col == 0 and c0.box == 0

# cell at index 10 → row 1, col 1, box 0
c10 = board.cells[10]
assert c10.row == 1 and c10.col == 1 and c10.box == 0

# cell at index 20 → row 2, col 2, box 0
c20 = board.cells[20]
assert c20.row == 2 and c20.col == 2 and c20.box == 0

# cell at index 40 → row 4, col 4, box 4
c40 = board.cells[40]
assert c40.row == 4 and c40.col == 4 and c40.box == 4

# cell at index 80 → row 8, col 8, box 8
c80 = board.cells[80]
assert c80.row == 8 and c80.col == 8 and c80.box == 8

# ------------------------------------------------------------------
# 4. Givens: singleton domain and correct value
# ------------------------------------------------------------------
# PUZZLE[0] == '5'  → index 0
assert board.cells[0].value == 5
assert board.cells[0].domain == {5}
assert board.cells[0].is_fixed

# PUZZLE[1] == '3'  → index 1
assert board.cells[1].value == 3
assert board.cells[1].domain == {3}

# ------------------------------------------------------------------
# 5. Empty cells: domain {1..9} and value 0
# ------------------------------------------------------------------
# PUZZLE[2] == '.'  → index 2
assert board.cells[2].value == 0
assert board.cells[2].domain == set(range(1, 10))
assert not board.cells[2].is_fixed

# ------------------------------------------------------------------
# 6. get_cell(row, col) returns the expected cell
# ------------------------------------------------------------------
assert board.get_cell(0, 0) is board.cells[0]
assert board.get_cell(4, 4) is board.cells[40]
assert board.get_cell(8, 8) is board.cells[80]

# ------------------------------------------------------------------
# 7. rc_to_index and index_to_rc are consistent
# ------------------------------------------------------------------
for idx in range(81):
    r, c = Board.index_to_rc(idx)
    assert Board.rc_to_index(r, c) == idx, f"round-trip failed at index {idx}"

# ------------------------------------------------------------------
# 8. copy() returns an independent deep copy
# ------------------------------------------------------------------
board_copy = board.copy()
assert board_copy is not board
assert board_copy.cells is not board.cells
board_copy.cells[0].value = 9
assert board.cells[0].value == 5, "original must not be affected by copy mutation"

# ------------------------------------------------------------------
# 9. Invalid puzzle length raises ValueError
# ------------------------------------------------------------------
try:
    Board.from_string("123")
    assert False, "should have raised ValueError for short string"
except ValueError:
    pass

# ------------------------------------------------------------------
# 10. Invalid character raises ValueError
# ------------------------------------------------------------------
bad_puzzle = "x" + PUZZLE[1:]   # replace first char with 'x'
try:
    Board.from_string(bad_puzzle)
    assert False, "should have raised ValueError for invalid character"
except ValueError:
    pass

# ------------------------------------------------------------------
# 11. is_solved() and is_valid_solution() return True for a solved board
# ------------------------------------------------------------------
import sys as _sys
_sys.path.insert(0, _sys.path[0])  # already inserted at top
from sudoku.propagator import ConstraintPropagator as _CP

solved_board = Board.from_string(PUZZLE)
_CP.initialize(solved_board)
assert solved_board.is_solved(),            "initialized easy puzzle must be solved"
assert solved_board.is_valid_solution(),    "initialized easy puzzle must be a valid solution"

# ------------------------------------------------------------------
# 12. is_solved() returns False for an un-initialized board
# ------------------------------------------------------------------
blank = Board.from_string("." * 81)
assert not blank.is_solved(),           "blank board must not be solved"
assert not blank.is_valid_solution(),   "blank board must not be a valid solution"

print("All 12 test cases passed.")
