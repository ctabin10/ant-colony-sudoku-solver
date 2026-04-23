# Ant Colony Optimization Sudoku Solver

## 1. The Problem

Sudoku is a number puzzle played on a 9×9 grid. The goal is to fill every cell with a digit from 1 to 9 such that no digit repeats in any row, column, or 3×3 box.

From a computer science perspective, Sudoku is a **constraint satisfaction problem (CSP)**. Each empty cell is a variable, its legal digits are its domain, and the no-repeat rules are the constraints. The challenge is that choices interact: filling in one cell restricts what its neighbours can be.

Brute force (trying every possible combination) is impractical. A 9×9 grid can have up to 6.67 × 10²¹ possible fillings before constraints are applied. The key to solving Sudoku efficiently is to reason about constraints before guessing.

---

## 2. Approach Overview

This solver combines two techniques:

1. **Constraint propagation** — logical deduction that shrinks the set of legal values for each cell. When a digit is assigned to a cell, it is removed from the domains of all cells that share a row, column, or box. This often forces other cells to be resolved automatically, without guessing.

2. **Ant Colony Optimization (ACO)** — a probabilistic search method inspired by how ants find food. When propagation alone cannot solve the puzzle, artificial ants build candidate solutions by making guided digit choices. Each ant leaves a pheromone trail on the choices it made; better choices accumulate more pheromone and are preferred in future iterations.

Together, propagation reduces the search space dramatically, and ACO explores what remains intelligently.

---

## 3. System Architecture

The project is split into two packages — `sudoku/` for puzzle representation and logic, and `aco/` for the search algorithm — plus a top-level entry point.

### 3.1 Cell — `sudoku/cell.py`

A `Cell` represents one variable in the CSP.

- `index` — flat position 0–80 in the grid (row-major order).
- `row`, `col`, `box` — group memberships used to build constraints.
- `domain` — the set of digits still legal for this cell. This is the source of truth; `value` is always derived from it.
- `value` — the digit assigned to this cell, or 0 if unresolved. Updated by `sync_value_from_domain()`.
- `peers` — the 20 other cells that share a row, column, or box with this cell. A choice made here constrains all of them.

A cell is considered **fixed** when its domain has been narrowed to exactly one digit.

### 3.2 Board — `sudoku/board.py`

A `Board` holds all 81 cells and the structural information that ties them together.

- Cells are stored in a flat list (`cells[0..80]`), indexed row-by-row.
- `rows`, `cols`, and `boxes` are lists of index groups — each group names which cells belong to a unit.
- When a board is built from a puzzle string, peers are computed for every cell by unioning its row, column, and box members (excluding the cell itself).
- `from_string(puzzle)` parses an 81-character string where digits 1–9 are given values and `.` marks empty cells. Invalid characters or lengths raise `ValueError`.
- `is_solved()` confirms that every cell has a singleton domain and every unit contains exactly the digits 1–9.

### 3.3 Constraint Propagation — `sudoku/propagator.py`

`ConstraintPropagator` implements two operations that together handle most of Sudoku's logical deduction.

**`assign(board, cell, digit)`** — commits a digit to a cell by eliminating all other options from that cell's domain. Elimination cascades.

**`eliminate(board, cell, digit)`** — removes one digit from one cell's domain and checks two consequences:

- *Naked single*: if the domain shrinks to one value, that value must be the cell's digit. It is then eliminated from all 20 peers. Those eliminations may in turn force further cells, so this propagates recursively.
- *Hidden single*: after removing the digit from this cell, check whether the digit still has a legal home in each of this cell's units (row, column, box). If it can only go in one remaining cell of a unit, it is assigned there immediately.

A **contradiction** is detected when a cell's domain becomes empty (no legal value exists) or when a digit has no legal cell left in a unit. Either signals that the current assignment path is invalid.

**`initialize(board)`** re-applies all given digits through `assign()` so that propagation fires from a clean slate. Easy puzzles are fully solved here, before any search is needed.

### 3.4 Pheromone Matrix — `aco/pheromone.py`

The `PheromoneMatrix` stores a desirability score for every `(cell, digit)` pair — an 81×10 table of floats (column 0 is unused; digits index directly as 1–9).

All entries start at `tau0 = 1/81`, a uniform baseline. As the search runs, entries for good choices accumulate higher values.

The **local update rule** is applied each time an ant makes a choice:

```
new_tau = (1 - xi) * old_tau + xi * tau0
```

This slightly decays the trail toward the baseline immediately after a visit, discouraging other ants from blindly following the same path and keeping the search diverse.

### 3.5 Value Chooser — `aco/chooser.py`

`ValueChooser` decides which digit to assign to one unresolved cell.

A random number `q` is drawn:

- If `q < q0` (default 0.9): **greedy** — pick the digit with the highest pheromone among the cell's current legal domain. Ties are broken deterministically by taking the smallest digit.
- Otherwise: **roulette** — sample proportionally to pheromone weights. Digits with higher pheromone are more likely but not certain to be chosen. If all weights are zero, fall back to uniform random.

The high default for `q0` means ants usually exploit the best-known information, but occasionally explore alternatives.

Only digits that remain in the cell's legal domain at the moment of the choice are ever considered. Digits ruled out by propagation are never selected.

### 3.6 Ant and AntSolver — `aco/ant.py`, `aco/ant_solver.py`

An `Ant` carries its own independent copy of the board and walks through all 81 cells, visiting them in a cycle starting from its assigned start index.

`AntSolver.step()` handles one cell visit:

- **Already fixed** (resolved by propagation): skip and advance.
- **Empty domain**: contradiction — mark the ant as failed.
- **Unresolved**: choose a digit using `ValueChooser`, call `assign()`, apply a local pheromone update, and advance. If the assignment fails (contradiction downstream), mark the ant as failed.

The ant's `path` records only the digits it chose explicitly. Digits fixed by propagation cascading from those choices are not recorded — the path reflects decisions, not consequences.

`AntSolver.run_ant()` calls `step()` up to 81 times and counts how many cells ended up fixed.

### 3.7 Colony — `aco/colony.py`

`Colony` manages a group of ants working together on the same puzzle.

Each iteration:

1. **Create ants** — each ant gets an independent board copy and a distinct randomised start index so they explore different parts of the grid.
2. **Interleaved stepping** — rather than running each ant to completion before the next begins, all ants take one step per round for 81 rounds. This lets pheromone updates from one ant influence others in near-real time.
3. **Select best ant** — prefer non-failed ants; among those, pick the one with the most fixed cells.
4. **Update global best memory** — if the best ant's reward (`81 / (81 − num_fixed)`) exceeds the best seen so far, store it.
5. **Global pheromone update** — strengthen the pheromone along the best-known path:

   ```
   new_tau = (1 - rho) * old_tau + rho * best_reward_so_far
   ```

6. **Best-value evaporation (BVE)** — gently decay `best_reward_so_far` each iteration. This prevents the solver from locking onto a past solution that may no longer be reachable and keeps the search from stagnating.

### 3.8 Solver — `aco/solver.py`

`SudokuACOSolver` is the single entry point that ties everything together.

1. Parse and validate the puzzle string.
2. Run constraint propagation. If it finds a contradiction, raise `ValueError`. If it solves the puzzle outright, return immediately.
3. Otherwise, create a colony and loop for up to `max_iterations`.
4. Each iteration, record the best ant's `num_fixed` in `history` and update the best board seen.
5. Return the solved board as soon as one is found, or the best partial result if the iteration limit is reached.

---

## 4. Key Ideas

- **Domain-based reasoning**: the `domain` set is the source of truth for every cell. Assigning or eliminating values is always done through the domain, never by direct manipulation of `value`.
- **Propagation reduces complexity**: most easy puzzles are solved before any probabilistic search is needed, making the ACO loop cheap or unnecessary.
- **ACO balances exploration and exploitation**: the `q0` parameter controls how often ants follow the best-known path versus sampling randomly. Local pheromone decay keeps early good paths from monopolising the search.
- **Best-value evaporation prevents stagnation**: decaying the reward signal forces the colony to keep improving rather than circling a local optimum indefinitely.

---

## 5. How to Run

```bash
python main.py
```

This solves the built-in sample puzzle and prints the completed board along with whether it was solved and how many ACO iterations were needed.

---

## 6. Project Structure

```
ant-colony-sudoku-solver/
│
├── sudoku/
│   ├── __init__.py
│   ├── cell.py               # Cell dataclass — one grid variable
│   ├── board.py              # Board dataclass — structure and validation
│   └── propagator.py         # Constraint propagation (assign / eliminate)
│
├── aco/
│   ├── __init__.py
│   ├── pheromone.py          # Pheromone matrix and local update rule
│   ├── chooser.py            # Greedy / roulette digit selection
│   ├── ant.py                # Ant state
│   ├── ant_solver.py         # Ant stepping logic
│   ├── colony.py             # Colony iteration and pheromone memory
│   └── solver.py             # Top-level orchestrator
│
├── evaluation/
│   ├── __init__.py
│   ├── puzzle_source.py      # Puzzle generation grouped by difficulty bucket
│   ├── metrics.py            # BenchmarkResult dataclass and summarize_results()
│   ├── benchmark.py          # Single-run benchmark: solve, time, and save CSVs
│   ├── experiment_runner.py  # Multi-run baseline experiment with averaged summaries
│   └── results/
│       ├── raw_results.csv
│       ├── summary.csv
│       └── baseline_results.csv
│
├── test/
│   ├── test_cell.py
│   ├── test_board.py
│   ├── test_propagator.py
│   ├── test_pheromone.py
│   ├── test_chooser.py
│   ├── test_ant.py
│   ├── test_colony.py
│   ├── test_solver.py
│   ├── test_puzzle_source.py
│   ├── test_metrics.py
│   └── test_benchmark.py
│
├── generator.py
└── main.py
```

---

## 7. Evaluation Pipeline

The `evaluation/` package provides a layered pipeline for measuring solver performance at scale.

**`puzzle_source.py`** — generates puzzles using the `dokusan` library, grouped into four difficulty buckets. Each bucket label maps to a numeric `avg_rank` that controls how constrained the generated puzzle is:

| Label | avg\_rank | Typical empty cells |
|--------|-----------|---------------------|
| easy | 30 | ~32 |
| medium | 50 | ~40 |
| hard | 100 | ~53 |
| expert | 200 | ~55 |

**`metrics.py`** — defines `BenchmarkResult`, a dataclass that records one puzzle run (solved status, time, history length, propagation-only flag, and error). `summarize_results()` aggregates a list of results into per-bucket statistics.

**`benchmark.py`** — runs one full benchmark: generates puzzles, solves each one, and writes raw and summary CSVs. Run it directly:

```bash
python evaluation/benchmark.py
```

**`experiment_runner.py`** — repeats the benchmark a configurable number of times and averages the results across runs. This is the main tool for producing stable performance estimates:

```bash
python evaluation/experiment_runner.py
```

---

## 8. Testing

All tests use plain Python assertions and can be run directly without any test framework.

```bash
python test/test_cell.py
python test/test_board.py
python test/test_propagator.py
python test/test_pheromone.py
python test/test_chooser.py
python test/test_ant.py
python test/test_colony.py
python test/test_solver.py
python test/test_puzzle_source.py
python test/test_metrics.py
python test/test_benchmark.py
```

---

## 9. Baseline Experiment Results

The baseline experiment was run with a deliberately minimal ACO configuration to establish a lower bound on solver performance and to measure how much work constraint propagation alone can handle.

### Configuration

| Parameter | Value |
|-----------|-------|
| NUM\_RUNS | 10 |
| NUM\_PER\_BUCKET | 100 |
| NUM\_ANTS | 1 |
| MAX\_ITERATIONS | 10 |
| Total puzzle attempts | 4,000 |

### Results

| Bucket | Avg Solved Rate | Avg Mean Time (s) | Avg Prop-only |
|--------|----------------|-------------------|---------------|
| easy | 100.0% | 0.0023 | 100.0 |
| medium | 100.0% | 0.0024 | 99.4 |
| hard | 99.2% | 0.0044 | 85.5 |
| expert | 94.7% | 0.0098 | 56.6 |
| **overall** | **98.5%** | **0.0047** | **85.4** |

### Discussion

**Propagation carries almost all the load.** Across all 4,000 puzzle attempts, constraint propagation alone solved 85.4% of puzzles on average before the ACO loop was even entered. Every single easy puzzle and essentially all medium puzzles (99.4 out of 100 per run) were resolved by `ConstraintPropagator.initialize()` without any search. This confirms that the CSP structure of Sudoku is dense enough that logical deduction is the dominant solver — ACO is the exception, not the rule.

**Performance degrades gracefully with difficulty.** The solve rate drops from 100% at easy and medium to 99.2% at hard and 94.7% at expert. The mean solve time increases from ~2 ms at easy to ~10 ms at expert. This gradient is exactly what we should expect: harder puzzles leave more cells unresolved after propagation, giving ACO more ground to cover within its 10-iteration budget.

**The ACO configuration is intentionally weak.** Using only 1 ant and 10 iterations is far below any production setting — this run was designed to stress the propagation layer, not the search layer. The fact that the solver still achieves 94.7% on expert puzzles under these constraints is encouraging. It suggests the pheromone and propagation integration is working correctly, and that scaling up ants and iterations should yield meaningful improvement on the unsolved cases.

**The 5.3% expert failure rate is the primary target for future tuning.** All failures at expert occur because the 10-iteration budget runs out before a full solution is found. The returned board in those cases is a partial result (the best seen during the run), not a contradiction. Increasing `MAX_ITERATIONS` or `NUM_ANTS` is the most direct lever for closing this gap.

---

## 10. Notes

- **Easy puzzles** (those solvable by logical deduction alone) are solved entirely by `ConstraintPropagator.initialize()`. The ACO loop is never entered and `history` stays empty.
- **Harder puzzles** require the ACO search. The solver returns the best board found within `max_iterations`; if no complete solution is found, the most-complete partial board is returned.
