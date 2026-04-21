"""Tests for aco.pheromone.PheromoneMatrix — run with: python test/test_pheromone.py"""

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aco.pheromone import PheromoneMatrix

# ------------------------------------------------------------------
# 1. Default matrix shape and initial values
# ------------------------------------------------------------------
pm = PheromoneMatrix()
assert len(pm.values) == 81, "must have 81 rows"
for row in pm.values:
    assert len(row) == 10, "each row must have 10 columns"
for ci in range(81):
    for d in range(1, 10):
        assert pm.values[ci][d] == pm.tau0, \
            f"values[{ci}][{d}] should equal tau0 at init"

# ------------------------------------------------------------------
# 2. get() returns the initialized value
# ------------------------------------------------------------------
assert pm.get(0, 1) == pm.tau0
assert pm.get(40, 5) == pm.tau0
assert pm.get(80, 9) == pm.tau0

# ------------------------------------------------------------------
# 3. set() updates the entry correctly
# ------------------------------------------------------------------
pm.set(10, 3, 0.75)
assert pm.get(10, 3) == 0.75, "set() must store the new value"
assert pm.get(10, 4) == pm.tau0, "adjacent entry must remain unchanged"

# ------------------------------------------------------------------
# 4. local_update() numerical correctness
#    tau0=0.1, old=0.5, xi=0.1 → (0.9 * 0.5) + (0.1 * 0.1) = 0.45 + 0.01 = 0.46
# ------------------------------------------------------------------
pm4 = PheromoneMatrix(tau0=0.1)
pm4.set(5, 2, 0.5)
pm4.local_update(5, 2, xi=0.1)
assert math.isclose(pm4.get(5, 2), 0.46, rel_tol=1e-9), \
    f"expected 0.46, got {pm4.get(5, 2)}"

# ------------------------------------------------------------------
# 5. local_update() leaves value unchanged when old == tau0
#    (1 - xi) * tau0 + xi * tau0 = tau0
# ------------------------------------------------------------------
pm5 = PheromoneMatrix(tau0=0.2)
pm5.local_update(0, 1, xi=0.3)
assert math.isclose(pm5.get(0, 1), 0.2, rel_tol=1e-9), \
    "local_update at tau0 must be a no-op"

# ------------------------------------------------------------------
# 6. get() raises ValueError for invalid cell_index
# ------------------------------------------------------------------
try:
    pm.get(81, 1)
    assert False, "should raise ValueError for cell_index 81"
except ValueError:
    pass

try:
    pm.get(-1, 1)
    assert False, "should raise ValueError for cell_index -1"
except ValueError:
    pass

# ------------------------------------------------------------------
# 7. get() raises ValueError for invalid digit
# ------------------------------------------------------------------
try:
    pm.get(0, 0)
    assert False, "should raise ValueError for digit 0"
except ValueError:
    pass

try:
    pm.get(0, 10)
    assert False, "should raise ValueError for digit 10"
except ValueError:
    pass

# ------------------------------------------------------------------
# 8. set() raises ValueError for invalid cell_index
# ------------------------------------------------------------------
try:
    pm.set(100, 5, 0.5)
    assert False, "should raise ValueError for cell_index 100"
except ValueError:
    pass

# ------------------------------------------------------------------
# 9. set() raises ValueError for invalid digit
# ------------------------------------------------------------------
try:
    pm.set(0, 0, 0.5)
    assert False, "should raise ValueError for digit 0"
except ValueError:
    pass

# ------------------------------------------------------------------
# 10. local_update() raises ValueError for invalid digit
# ------------------------------------------------------------------
try:
    pm.local_update(0, 10)
    assert False, "should raise ValueError for digit 10"
except ValueError:
    pass

print("All 10 test cases passed.")
