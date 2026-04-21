"""Represents a single cell in a 9x9 Sudoku grid."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Cell:
    """One cell in a Sudoku grid.

    Attributes:
        index:  Flat index 0-80 (row-major order).
        row:    Row index 0-8.
        col:    Column index 0-8.
        box:    3x3 box index 0-8 (row-major over boxes).
        value:  Assigned digit 1-9, or 0 when unassigned.
        domain: Set of digits still legal for this cell.
        peers:  Flat indices of cells that share a row, column, or box
                with this cell (excludes self).
    """

    index: int
    row: int
    col: int
    box: int
    value: int = 0
    domain: set[int] = field(default_factory=lambda: set(range(1, 10)))
    peers: set[int] = field(default_factory=set)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_fixed(self) -> bool:
        """Return True when the domain has been narrowed to exactly one digit."""
        return len(self.domain) == 1

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    def sync_value_from_domain(self) -> None:
        """Keep ``value`` consistent with the current domain.

        * Singleton domain  → ``value`` becomes that digit.
        * Multi-value domain → ``value`` becomes 0 (unassigned).
        """
        if len(self.domain) == 1:
            (self.value,) = self.domain
        else:
            self.value = 0

    def fix(self, digit: int) -> None:
        """Assign *digit* to this cell: collapse domain to ``{digit}`` and set value.

        Args:
            digit: A legal Sudoku digit (1-9).

        Raises:
            ValueError: If *digit* is outside the range 1..9.
        """
        if not 1 <= digit <= 9:
            raise ValueError(f"Digit must be in 1..9, got {digit}.")
        self.domain = {digit}
        self.value = digit
