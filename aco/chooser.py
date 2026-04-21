"""Digit-selection logic for one Sudoku cell using ACO pheromone guidance."""

from __future__ import annotations
import random
from dataclasses import dataclass, field

from sudoku.board import Board
from aco.pheromone import PheromoneMatrix


@dataclass
class ValueChooser:
    """Chooses a digit for a single unresolved Sudoku cell.

    Uses a pseudo-random proportional rule:

    * Draw ``q`` from uniform [0, 1).
    * If ``q < q0``: greedy — pick the highest-pheromone legal digit.
    * Otherwise: roulette — pick proportionally to pheromone weights.

    Only digits present in the cell's current domain are candidates.

    Attributes:
        pheromone: Shared pheromone matrix.
        q0:        Greedy-choice probability threshold (default 0.9).
        rng:       Random source; injectable for deterministic testing.
    """

    pheromone: PheromoneMatrix
    q0: float = 0.9
    rng: random.Random = field(default_factory=random.Random)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def choose(self, board: Board, cell_index: int) -> int:
        """Choose a digit for the cell at *cell_index*.

        Args:
            board:      The current board (read-only; never mutated).
            cell_index: Flat cell index 0-80.

        Returns:
            A digit from the cell's legal domain.

        Raises:
            ValueError: If the cell's domain is empty.
        """
        domain = board.cells[cell_index].domain
        if not domain:
            raise ValueError(f"Cell {cell_index} has an empty domain; cannot choose.")
        if len(domain) == 1:
            return next(iter(domain))

        q = self.rng.random()
        if q < self.q0:
            return self._greedy_choice(cell_index, domain)
        return self._roulette_choice(cell_index, domain)

    # ------------------------------------------------------------------
    # Private selection strategies
    # ------------------------------------------------------------------

    def _greedy_choice(self, cell_index: int, domain: set[int]) -> int:
        """Return the legal digit with the highest pheromone level.

        Iterates over ``sorted(domain)`` so that the first maximum found
        is the smallest digit among any ties.
        """
        candidates = sorted(domain)
        return max(candidates, key=lambda d: self.pheromone.get(cell_index, d))

    def _roulette_choice(self, cell_index: int, domain: set[int]) -> int:
        """Return a digit sampled proportionally to pheromone weights.

        Falls back to uniform random over legal digits when every weight
        is zero (or the total is non-positive).
        """
        candidates = sorted(domain)
        weights = [self.pheromone.get(cell_index, d) for d in candidates]
        total = sum(weights)

        if total <= 0.0:
            return self.rng.choice(candidates)

        r = self.rng.random() * total
        cumulative = 0.0
        for d, w in zip(candidates, weights):
            cumulative += w
            if r < cumulative:
                return d
        return candidates[-1]  # guard against floating-point overshoot
