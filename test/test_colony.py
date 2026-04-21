"""Tests for aco.colony.Colony — run with: python test/test_colony.py"""

import sys
import os
import math
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sudoku.board import Board
from aco.ant import Ant
from aco.pheromone import PheromoneMatrix
from aco.chooser import ValueChooser
from aco.colony import Colony

BLANK = "." * 81
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


def make_ant(base: Board, start: int, failed: bool, num_fixed: int) -> Ant:
    a = Ant(board=base.copy(), start_index=start, current_index=start)
    a.failed = failed
    a.num_fixed = num_fixed
    return a


# ------------------------------------------------------------------
# 1. make_ants creates the right number of ants with distinct starts
#    and independent board copies
# ------------------------------------------------------------------
base = Board.from_string(PUZZLE)
colony1 = Colony(pheromone=PheromoneMatrix(), num_ants=5, rng=random.Random(7))
ants1 = colony1.make_ants(base)

assert len(ants1) == 5, "must create exactly num_ants ants"
assert len({a.start_index for a in ants1}) == 5, "start indices must be distinct"
for a in ants1:
    assert a.board is not base,           "board must be a copy, not the original"
    assert a.board.cells is not base.cells, "cells list must be independent"

# ------------------------------------------------------------------
# 2. make_chooser uses colony's pheromone and q0
# ------------------------------------------------------------------
pm2 = PheromoneMatrix()
colony2 = Colony(pheromone=pm2, q0=0.75, rng=random.Random(0))
chooser2 = colony2.make_chooser()

assert chooser2.pheromone is pm2,    "chooser must reference colony's pheromone"
assert chooser2.q0 == 0.75,          "chooser q0 must match colony q0"

# ------------------------------------------------------------------
# 3. select_best_ant prefers non-failed ants
# ------------------------------------------------------------------
colony3 = Colony(pheromone=PheromoneMatrix())
ant_good = make_ant(base, 0, failed=False, num_fixed=30)
ant_bad  = make_ant(base, 1, failed=True,  num_fixed=50)  # higher but failed

best3 = colony3.select_best_ant([ant_good, ant_bad])
assert best3 is ant_good, "non-failed ant must be preferred over failed ant"

# ------------------------------------------------------------------
# 4. If all ants failed, select_best_ant returns the one with highest num_fixed
# ------------------------------------------------------------------
ant_fa = make_ant(base, 0, failed=True, num_fixed=20)
ant_fb = make_ant(base, 1, failed=True, num_fixed=40)
best4 = colony3.select_best_ant([ant_fa, ant_fb])
assert best4 is ant_fb, "among all-failed ants, highest num_fixed must win"

# ------------------------------------------------------------------
# 5. compute_delta_tau numerical correctness
#    num_fixed=60 → 81 / (81-60) = 81/21
# ------------------------------------------------------------------
colony5 = Colony(pheromone=PheromoneMatrix())
ant5 = make_ant(base, 0, failed=False, num_fixed=60)
dt = colony5.compute_delta_tau(ant5)
assert math.isclose(dt, 81 / 21, rel_tol=1e-9), f"expected {81/21}, got {dt}"

# Solved board → inf
ant5_solved = make_ant(base, 0, failed=False, num_fixed=81)
assert colony5.compute_delta_tau(ant5_solved) == float("inf")

# ------------------------------------------------------------------
# 6. update_global_best_memory updates when reward improves
# ------------------------------------------------------------------
colony6 = Colony(pheromone=PheromoneMatrix())
ant6 = make_ant(base, 0, failed=False, num_fixed=60)
colony6.update_global_best_memory(ant6)

expected_dt6 = 81 / 21
assert math.isclose(colony6.best_reward_so_far, expected_dt6, rel_tol=1e-9), \
    "best_reward_so_far must be updated"
assert colony6.global_best_ant is ant6, "global_best_ant must be set"

# ------------------------------------------------------------------
# 7. update_global_best_memory does not update when reward is worse
# ------------------------------------------------------------------
colony7 = Colony(pheromone=PheromoneMatrix())
ant7_old = make_ant(base, 0, failed=False, num_fixed=60)
colony7.global_best_ant = ant7_old
colony7.best_reward_so_far = 100.0

ant7_worse = make_ant(base, 1, failed=False, num_fixed=60)  # same delta < 100
colony7.update_global_best_memory(ant7_worse)
assert colony7.best_reward_so_far == 100.0,      "reward must not decrease"
assert colony7.global_best_ant is ant7_old,       "global_best_ant must not change"

# ------------------------------------------------------------------
# 8. global_update applies the formula to pheromone entries in the path
#    new_tau = (1 - rho) * old_tau + rho * best_reward_so_far
# ------------------------------------------------------------------
pm8 = PheromoneMatrix()
colony8 = Colony(pheromone=pm8, rho=0.9)
colony8.best_reward_so_far = 4.0

ant8 = make_ant(base, 0, failed=False, num_fixed=70)
ant8.path = [(0, 5), (10, 3)]
colony8.global_best_ant = ant8

old_05  = pm8.get(0, 5)
old_103 = pm8.get(10, 3)
old_01  = pm8.get(0, 1)   # not in path — must be unchanged
colony8.global_update()

exp_05  = (1.0 - 0.9) * old_05  + 0.9 * 4.0
exp_103 = (1.0 - 0.9) * old_103 + 0.9 * 4.0
assert math.isclose(pm8.get(0, 5),  exp_05,  rel_tol=1e-9), "pheromone (0,5) incorrect"
assert math.isclose(pm8.get(10, 3), exp_103, rel_tol=1e-9), "pheromone (10,3) incorrect"
assert math.isclose(pm8.get(0, 1),  old_01,  rel_tol=1e-9), "pheromone (0,1) must be unchanged"

# ------------------------------------------------------------------
# 9. best_value_evaporation reduces best_reward_so_far correctly
#    8.0 * (1 - 0.005) = 7.96
# ------------------------------------------------------------------
colony9 = Colony(pheromone=PheromoneMatrix(), rho_bve=0.005)
colony9.best_reward_so_far = 8.0
colony9.best_value_evaporation()
assert math.isclose(colony9.best_reward_so_far, 7.96, rel_tol=1e-9), \
    f"expected 7.96, got {colony9.best_reward_so_far}"

# ------------------------------------------------------------------
# 10. run_iteration returns ants + best_ant and does not mutate base_board
# ------------------------------------------------------------------
base10 = Board.from_string(PUZZLE)
original_domains = [frozenset(c.domain) for c in base10.cells]

colony10 = Colony(pheromone=PheromoneMatrix(), num_ants=3, rng=random.Random(0))
ants10, best10 = colony10.run_iteration(base10)

assert len(ants10) == 3,       "must return exactly num_ants ants"
assert best10 in ants10,       "best_ant must be from the returned list"
for i, cell in enumerate(base10.cells):
    assert frozenset(cell.domain) == original_domains[i], \
        f"base_board cell {i} was mutated by run_iteration"

# ------------------------------------------------------------------
# 11. run_one_iteration updates colony memory and applies BVE
#     Strategy: run the iteration, then back-compute the pre-BVE reward
#     from the stored global_best_ant.num_fixed and verify it matches.
#     This works regardless of whether ants solve the puzzle or not.
# ------------------------------------------------------------------
colony11 = Colony(pheromone=PheromoneMatrix(), num_ants=3, rng=random.Random(1))
ants11, best11 = colony11.run_one_iteration(Board.from_string(PUZZLE))

assert isinstance(ants11, list) and len(ants11) == 3, "must return num_ants ants"
assert best11 in ants11,                               "best_ant must be from the list"
assert colony11.global_best_ant is not None,           "global_best_ant must be set"

# BVE verification: best_reward_so_far = delta_tau * (1 - rho_bve)
dt11 = colony11.compute_delta_tau(colony11.global_best_ant)
if math.isinf(dt11):
    assert math.isinf(colony11.best_reward_so_far), \
        "solved puzzle: best_reward_so_far must be inf"
else:
    expected11 = dt11 * (1.0 - colony11.rho_bve)
    assert math.isclose(colony11.best_reward_so_far, expected11, rel_tol=1e-9), \
        f"BVE not applied: expected {expected11}, got {colony11.best_reward_so_far}"

print("All 11 test cases passed.")
