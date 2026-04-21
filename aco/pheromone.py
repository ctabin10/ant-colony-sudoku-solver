"""Pheromone matrix for the Sudoku ACO solver."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class PheromoneMatrix:
    """Stores pheromone levels for every (cell, digit) pair.

    Layout: ``values[cell_index][digit]`` where cell_index is 0-80 and
    digit is 1-9.  Column 0 of each row is allocated but unused so that
    digits can be used as direct indices without an offset.

    Attributes:
        tau0:   Initial (and evaporation target) pheromone level.
        values: 81 x 10 matrix; access as values[cell_index][digit].
    """

    tau0: float = 1.0 / 81.0
    values: list[list[float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.values:
            self.values = [
                [self.tau0] * 10
                for _ in range(81)
            ]

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _check(self, cell_index: int, digit: int) -> None:
        if not 0 <= cell_index <= 80:
            raise ValueError(f"cell_index must be 0..80, got {cell_index}.")
        if not 1 <= digit <= 9:
            raise ValueError(f"digit must be 1..9, got {digit}.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get(self, cell_index: int, digit: int) -> float:
        """Return the pheromone level for (cell_index, digit)."""
        self._check(cell_index, digit)
        return self.values[cell_index][digit]

    def set(self, cell_index: int, digit: int, value: float) -> None:
        """Set the pheromone level for (cell_index, digit) to *value*."""
        self._check(cell_index, digit)
        self.values[cell_index][digit] = value

    def local_update(self, cell_index: int, digit: int, xi: float = 0.1) -> None:
        """Apply the local pheromone update rule.

        ``new_tau = (1 - xi) * old_tau + xi * tau0``

        This nudges the trail back toward the initial level after each
        ant visits a cell, preventing premature convergence.

        Args:
            cell_index: Flat cell index 0-80.
            digit:      Digit 1-9.
            xi:         Evaporation coefficient (default 0.1).
        """
        self._check(cell_index, digit)
        old = self.values[cell_index][digit]
        self.values[cell_index][digit] = (1.0 - xi) * old + xi * self.tau0
