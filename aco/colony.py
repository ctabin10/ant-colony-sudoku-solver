"""Colony management and pheromone memory for the Sudoku ACO solver."""

from __future__ import annotations
import random
from dataclasses import dataclass, field

from sudoku.board import Board
from aco.ant import Ant
from aco.ant_solver import AntSolver
from aco.chooser import ValueChooser
from aco.pheromone import PheromoneMatrix


@dataclass
class Colony:
    """Manages one ACO colony: ant creation, interleaved stepping,
    global pheromone memory, and best-value evaporation.

    Attributes:
        pheromone:           Shared pheromone matrix used by all ants.
        num_ants:            Number of ants per iteration.
        q0:                  Greedy-choice probability for ValueChooser.
        xi:                  Local evaporation coefficient (per-step).
        rho:                 Global update evaporation coefficient.
        rho_bve:             Best-value evaporation rate applied each iteration.
        rng:                 Shared random source; injectable for testing.
        best_reward_so_far:  Highest delta_tau seen across all iterations.
        global_best_ant:     Ant that achieved best_reward_so_far.
    """

    pheromone: PheromoneMatrix
    num_ants: int = 10
    q0: float = 0.9
    xi: float = 0.1
    rho: float = 0.9
    rho_bve: float = 0.005
    rng: random.Random = field(default_factory=random.Random)
    best_reward_so_far: float = 0.0
    global_best_ant: Ant | None = None

    # ------------------------------------------------------------------
    # Ant construction
    # ------------------------------------------------------------------

    def make_ants(self, base_board: Board) -> list[Ant]:
        """Create ``num_ants`` ants from independent deep copies of *base_board*.

        Start indices are drawn without replacement from a shuffled 0-80 range
        so every ant begins at a different cell.

        Args:
            base_board: Template board; never mutated.

        Returns:
            List of freshly created Ant objects.
        """
        indices = list(range(81))
        self.rng.shuffle(indices)
        return [
            Ant(board=base_board.copy(), start_index=s, current_index=s)
            for s in indices[: self.num_ants]
        ]

    def make_chooser(self) -> ValueChooser:
        """Return a ValueChooser wired to the colony's pheromone, q0, and rng."""
        return ValueChooser(pheromone=self.pheromone, q0=self.q0, rng=self.rng)

    # ------------------------------------------------------------------
    # Ant evaluation
    # ------------------------------------------------------------------

    def select_best_ant(self, ants: list[Ant]) -> Ant:
        """Return the best ant from *ants*.

        Non-failed ants are preferred over failed ones.  Within either
        group the ant with the highest ``num_fixed`` is chosen.

        Args:
            ants: Non-empty list of ants after a completed run.

        Returns:
            The best ant (by num_fixed, preferring non-failed).
        """
        non_failed = [a for a in ants if not a.failed]
        pool = non_failed if non_failed else ants
        return max(pool, key=lambda a: a.num_fixed)

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def run_iteration(self, base_board: Board) -> tuple[list[Ant], Ant]:
        """Run one interleaved colony iteration.

        Ants are stepped in round-robin order: in each of 81 rounds every
        ant takes one step.  This lets ants share pheromone updates in
        real time rather than waiting until all ants finish.

        Args:
            base_board: Starting board state; never mutated.

        Returns:
            ``(ants, best_ant)`` where *best_ant* is selected by
            :meth:`select_best_ant`.
        """
        ants = self.make_ants(base_board)
        chooser = self.make_chooser()

        for _ in range(81):
            for ant in ants:
                AntSolver.step(ant, chooser, self.pheromone, xi=self.xi)

        for ant in ants:
            ant.num_fixed = sum(1 for cell in ant.board.cells if len(cell.domain) == 1)

        best_ant = self.select_best_ant(ants)
        return ants, best_ant

    # ------------------------------------------------------------------
    # Pheromone memory
    # ------------------------------------------------------------------

    def compute_delta_tau(self, best_ant: Ant, total_cells: int = 81) -> float:
        """Compute the reward signal for *best_ant*.

        ``delta_tau = total_cells / (total_cells - best_ant.num_fixed)``

        Returns ``float("inf")`` when all cells are fixed (puzzle solved).

        Args:
            best_ant:    Ant whose num_fixed drives the reward.
            total_cells: Grid size (default 81).

        Returns:
            Reward value as a float.
        """
        if best_ant.num_fixed >= total_cells:
            return float("inf")
        return total_cells / (total_cells - best_ant.num_fixed)

    def update_global_best_memory(self, best_ant: Ant, total_cells: int = 81) -> None:
        """Update global best if *best_ant* beats the stored reward.

        Args:
            best_ant:    Candidate ant from the current iteration.
            total_cells: Grid size (default 81).
        """
        delta = self.compute_delta_tau(best_ant, total_cells)
        if delta > self.best_reward_so_far:
            self.best_reward_so_far = delta
            self.global_best_ant = best_ant

    def global_update(self) -> None:
        """Apply the global pheromone update along the best-known path.

        For every ``(cell_index, digit)`` in ``global_best_ant.path``:

        ``new_tau = (1 - rho) * old_tau + rho * best_reward_so_far``

        Does nothing if ``global_best_ant`` is None.
        """
        if self.global_best_ant is None:
            return
        for cell_index, digit in self.global_best_ant.path:
            old_tau = self.pheromone.get(cell_index, digit)
            new_tau = (1.0 - self.rho) * old_tau + self.rho * self.best_reward_so_far
            self.pheromone.set(cell_index, digit, new_tau)

    def best_value_evaporation(self) -> None:
        """Decay ``best_reward_so_far`` by ``rho_bve`` to avoid stagnation.

        ``best_reward_so_far *= (1 - rho_bve)``
        """
        self.best_reward_so_far *= (1.0 - self.rho_bve)

    # ------------------------------------------------------------------
    # Top-level iteration entry point
    # ------------------------------------------------------------------

    def run_one_iteration(self, base_board: Board) -> tuple[list[Ant], Ant]:
        """Run a full iteration and update all colony memory.

        Sequence:
        1. Run interleaved ant stepping (:meth:`run_iteration`).
        2. Update global best memory (:meth:`update_global_best_memory`).
        3. Apply global pheromone update (:meth:`global_update`).
        4. Apply best-value evaporation (:meth:`best_value_evaporation`).

        Args:
            base_board: Starting board state; never mutated.

        Returns:
            ``(ants, best_ant)`` from this iteration.
        """
        ants, best_ant = self.run_iteration(base_board)
        self.update_global_best_memory(best_ant)
        self.global_update()
        self.best_value_evaporation()
        return ants, best_ant
