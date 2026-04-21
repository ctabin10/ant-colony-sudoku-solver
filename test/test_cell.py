"""Tests for sudoku.cell.Cell — run with: python test/test_cell.py"""

import sys
import os

# Allow `from sudoku.cell import Cell` when run from any working directory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.cell import Cell


# ------------------------------------------------------------------
# 1. Fresh cell with domain {1, 2, 3}
# ------------------------------------------------------------------
c = Cell(index=0, row=0, col=0, box=0, domain={1, 2, 3})
assert not c.is_fixed, "is_fixed should be False for a 3-element domain"
assert c.value == 0,   "value should be 0 when domain has multiple elements"

# ------------------------------------------------------------------
# 2. fix(5)
# ------------------------------------------------------------------
c.fix(5)
assert c.domain == {5}, "domain should collapse to {5}"
assert c.value == 5,    "value should be 5"
assert c.is_fixed,      "is_fixed should be True after fix(5)"

# ------------------------------------------------------------------
# 3. sync_value_from_domain with singleton domain
# ------------------------------------------------------------------
c2 = Cell(index=1, row=0, col=1, box=0, domain={7})
c2.sync_value_from_domain()
assert c2.value == 7, "sync should assign value 7 from singleton domain"

# ------------------------------------------------------------------
# 4. sync_value_from_domain with multi-element domain resets to 0
# ------------------------------------------------------------------
c3 = Cell(index=2, row=0, col=2, box=0, value=3, domain={3, 4, 5})
c3.sync_value_from_domain()
assert c3.value == 0, "sync should reset value to 0 for multi-element domain"

# ------------------------------------------------------------------
# 5. fix(0) raises ValueError
# ------------------------------------------------------------------
c4 = Cell(index=3, row=0, col=3, box=0)
try:
    c4.fix(0)
    assert False, "fix(0) should have raised ValueError"
except ValueError:
    pass

# ------------------------------------------------------------------
# 6. fix(10) raises ValueError
# ------------------------------------------------------------------
try:
    c4.fix(10)
    assert False, "fix(10) should have raised ValueError"
except ValueError:
    pass

print("All 6 test cases passed.")
