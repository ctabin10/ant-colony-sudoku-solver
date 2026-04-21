"""Top-level ACO orchestrator for solving a Sudoku puzzle."""

from __future__ import annotations
from dataclasses import dataclass, field

from sudoku.board import Board
from sudoku.propagator import ConstraintPropagator
from aco.pheromone import PheromoneMatrix
from aco.colony import Colony


@dataclass
class SudokuACOSolver:
    """Orchestrates the full ACO solve loop for a 9x9 Sudoku puzzle.

    Attributes:
        num_ants:       Colony size per iteration.
        max_iterations: Hard cap on iteration count.
        q0:             Greedy-choice probability for ValueChooser.
        xi:             Local evaporation coefficient.
        rho:            Global pheromone update coefficient.
        rho_bve:        Best-value evaporation rate.
        history:        ``(iteration, best_num_fixed)`` pairs from the last
                        ``solve()`` call; cleared at the start of every run.
    """

    num_ants: int = 10
    max_iterations: int = 200
    q0: float = 0.9
    xi: float = 0.1
    rho: float = 0.9
    rho_bve: float = 0.005
    history: list[tuple[int, int]] = field(default_factory=list)

    def solve(self, puzzle: str) -> Board:
        """Solve *puzzle* and return the best board found.

        Args:
            puzzle: 81-character puzzle string (digits 1-9 or '.').

        Returns:
            A fully solved Board if one is found within ``max_iterations``;
            otherwise the best (most-fixed) board seen during the run.

        Raises:
            ValueError: If the puzzle string is invalid or contradictory.
        """
        # Step 1: reset history for this run
        self.history.clear()

        # Step 2: build and propagate
        base_board = Board.from_string(puzzle)  # raises ValueError on bad string
        if not ConstraintPropagator.initialize(base_board):
            raise ValueError("Puzzle is invalid or contradictory.")

        # Step 3: propagation may already solve the puzzle
        if base_board.is_solved():
            return base_board

        # Step 4: initialise colony
        pheromone = PheromoneMatrix(tau0=1.0 / 81.0)
        colony = Colony(
            pheromone=pheromone,
            num_ants=self.num_ants,
            q0=self.q0,
            xi=self.xi,
            rho=self.rho,
            rho_bve=self.rho_bve,
        )

        # Step 5: track best board seen so far
        best_board_seen = base_board.copy()
        best_num_fixed = sum(1 for c in best_board_seen.cells if len(c.domain) == 1)

        # Step 6: main loop
        for iteration in range(self.max_iterations):
            ants, best_ant = colony.run_one_iteration(base_board)
            self.history.append((iteration, best_ant.num_fixed))

            if best_ant.num_fixed > best_num_fixed:
                best_num_fixed = best_ant.num_fixed
                best_board_seen = best_ant.board.copy()

            if best_ant.board.is_solved():
                return best_ant.board

        # Step 7: return best seen if no full solution was found
        return best_board_seen
