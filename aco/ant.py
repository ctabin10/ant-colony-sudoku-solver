"""Ant state for the Sudoku ACO solver."""

from __future__ import annotations
from dataclasses import dataclass, field

from sudoku.board import Board


@dataclass
class Ant:
    """Represents one ant traversing the Sudoku board.

    An ant walks cell by cell, choosing digits and recording only the
    decisions it made explicitly.  Assignments that result from constraint
    propagation triggered by a choice are *not* added to ``path`` — the
    path records only the ant's own choices.

    Attributes:
        board:         Working copy of the board this ant is solving.
        start_index:   Flat index where the ant began its walk (0-80).
        current_index: Flat index of the cell the ant will visit next.
        path:          Sequence of (cell_index, digit) pairs for each
                       digit the ant chose explicitly.
        num_fixed:     Number of singleton-domain cells after the run;
                       set by AntSolver.run_ant() upon completion.
        failed:        True if a contradiction was encountered; the board
                       state is then invalid and the ant's solution is
                       discarded.
    """

    board: Board
    start_index: int
    current_index: int
    path: list[tuple[int, int]] = field(default_factory=list)
    num_fixed: int = 0
    failed: bool = False
