"""Sudoku board: structure, grouping, and peer relationships."""

from __future__ import annotations
import copy
from dataclasses import dataclass, field

from sudoku.cell import Cell


@dataclass
class Board:
    """A 9x9 Sudoku board.

    Attributes:
        cells: All 81 cells in row-major order (index 0-80).
        rows:  rows[r]  — list of 9 flat indices for row r.
        cols:  cols[c]  — list of 9 flat indices for column c.
        boxes: boxes[b] — list of 9 flat indices for 3x3 box b.
    """

    cells: list[Cell]
    rows:  list[list[int]] = field(default_factory=list)
    cols:  list[list[int]] = field(default_factory=list)
    boxes: list[list[int]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Index helpers
    # ------------------------------------------------------------------

    @staticmethod
    def rc_to_index(row: int, col: int) -> int:
        """Convert (row, col) to a flat index 0-80."""
        return row * 9 + col

    @staticmethod
    def index_to_rc(index: int) -> tuple[int, int]:
        """Convert a flat index 0-80 to (row, col)."""
        return divmod(index, 9)

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(self, row: int, col: int) -> Cell:
        """Return the Cell at (row, col)."""
        return self.cells[Board.rc_to_index(row, col)]

    # ------------------------------------------------------------------
    # Copy
    # ------------------------------------------------------------------

    def copy(self) -> "Board":
        """Return an independent deep copy of this board."""
        return copy.deepcopy(self)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_string(cls, puzzle: str) -> "Board":
        """Build a Board from an 81-character puzzle string.

        Args:
            puzzle: Exactly 81 characters; digits 1-9 are givens, '.' is empty.

        Returns:
            A fully initialised Board with groups and peers populated.

        Raises:
            ValueError: If the string length is not 81 or contains an invalid character.
        """
        if len(puzzle) != 81:
            raise ValueError(f"Puzzle string must be 81 characters, got {len(puzzle)}.")

        cells: list[Cell] = []
        for idx, ch in enumerate(puzzle):
            r, c = divmod(idx, 9)
            b = (r // 3) * 3 + (c // 3)
            if ch in "123456789":
                digit = int(ch)
                cells.append(Cell(index=idx, row=r, col=c, box=b,
                                  value=digit, domain={digit}))
            elif ch == ".":
                cells.append(Cell(index=idx, row=r, col=c, box=b,
                                  value=0, domain=set(range(1, 10))))
            else:
                raise ValueError(f"Invalid puzzle character at index {idx}: {ch!r}")

        # Build groups of flat indices
        rows  = [[r * 9 + c for c in range(9)] for r in range(9)]
        cols  = [[r * 9 + c for r in range(9)] for c in range(9)]
        boxes = []
        for br in range(3):
            for bc in range(3):
                boxes.append([
                    (br * 3 + dr) * 9 + (bc * 3 + dc)
                    for dr in range(3)
                    for dc in range(3)
                ])

        # Assign peers: union of row + col + box mates, excluding self
        for cell in cells:
            row_peers = set(rows[cell.row])
            col_peers = set(cols[cell.col])
            box_peers = set(boxes[cell.box])
            cell.peers = (row_peers | col_peers | box_peers) - {cell.index}

        return cls(cells=cells, rows=rows, cols=cols, boxes=boxes)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        lines = []
        for r in range(9):
            if r in (3, 6):
                lines.append("------+-------+------")
            row_chars = []
            for c in range(9):
                if c in (3, 6):
                    row_chars.append("|")
                cell = self.get_cell(r, c)
                row_chars.append(str(cell.value) if cell.value != 0 else ".")
            lines.append(" ".join(row_chars))
        return "\n".join(lines)
