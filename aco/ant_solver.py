"""Ant stepping and run logic for the Sudoku ACO solver."""

from __future__ import annotations

from aco.ant import Ant
from aco.chooser import ValueChooser
from aco.pheromone import PheromoneMatrix
from sudoku.propagator import ConstraintPropagator


class AntSolver:
    """Drives a single ant through one full traversal of the board.

    All methods are static; ``AntSolver`` is a namespace, not a stateful object.
    """

    @staticmethod
    def step(
        ant: Ant,
        chooser: ValueChooser,
        pheromone: PheromoneMatrix,
        xi: float = 0.1,
    ) -> None:
        """Advance the ant by one cell.

        Three outcomes depending on the current cell's state:

        * **Already fixed** (singleton domain): skip — advance index only.
        * **Empty domain**: mark ant as failed and return.
        * **Unresolved** (multi-value domain): choose a digit, assign it,
          apply a local pheromone update, and advance.  If assignment
          causes a contradiction the ant is marked failed.

        Only the explicitly chosen cell is appended to ``ant.path``.
        Propagated singleton fixes are not recorded.

        Args:
            ant:      The ant to advance.
            chooser:  Digit-selection strategy.
            pheromone: Shared pheromone matrix for local updates.
            xi:       Local evaporation coefficient (default 0.1).
        """
        if ant.failed:
            return

        cell = ant.board.cells[ant.current_index]

        # Case A: cell already resolved by propagation — just move on
        if cell.is_fixed:
            ant.current_index = (ant.current_index + 1) % 81
            return

        # Case B: empty domain — contradiction
        if not cell.domain:
            ant.failed = True
            return

        # Case C: unresolved — choose, assign, update pheromone
        chosen_digit = chooser.choose(ant.board, ant.current_index)
        if not ConstraintPropagator.assign(ant.board, ant.current_index, chosen_digit):
            ant.failed = True
            return

        ant.path.append((ant.current_index, chosen_digit))
        pheromone.local_update(ant.current_index, chosen_digit, xi=xi)
        ant.current_index = (ant.current_index + 1) % 81

    @staticmethod
    def run_ant(
        ant: Ant,
        chooser: ValueChooser,
        pheromone: PheromoneMatrix,
        xi: float = 0.1,
    ) -> None:
        """Run the ant for up to 81 steps, then record how many cells are fixed.

        Stops early if the ant fails.  ``ant.num_fixed`` is always written
        at the end, even for a failed ant, so callers can inspect partial
        progress.

        Args:
            ant:      The ant to run.
            chooser:  Digit-selection strategy.
            pheromone: Shared pheromone matrix.
            xi:       Local evaporation coefficient (default 0.1).
        """
        for _ in range(81):
            if ant.failed:
                break
            AntSolver.step(ant, chooser, pheromone, xi=xi)

        ant.num_fixed = sum(
            1 for cell in ant.board.cells if len(cell.domain) == 1
        )
