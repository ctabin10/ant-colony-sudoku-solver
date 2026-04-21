"""Arc-consistency constraint propagation for Sudoku."""

from __future__ import annotations

from sudoku.board import Board


class ConstraintPropagator:
    """Propagates Sudoku constraints via elimination and unit-place forcing.

    All methods operate directly on the board passed in; callers that need
    to preserve the original state should pass a ``board.copy()``.
    """

    @staticmethod
    def assign(board: Board, index: int, digit: int) -> bool:
        """Force cell *index* to *digit* by eliminating every other value.

        Args:
            board: The board to mutate.
            index: Flat cell index 0-80.
            digit: The digit to assign (must already be in the cell's domain).

        Returns:
            True on success, False if a contradiction arises.
        """
        cell = board.cells[index]
        if digit not in cell.domain:
            return False
        other_digits = cell.domain - {digit}
        for d in other_digits:
            if not ConstraintPropagator.eliminate(board, index, d):
                return False
        return True

    @staticmethod
    def eliminate(board: Board, index: int, digit: int) -> bool:
        """Remove *digit* from cell *index*'s domain and propagate consequences.

        Four cases are handled in order:

        A. Digit already absent   → no-op, return True.
        B. Domain would go empty  → contradiction, return False.
        C. Domain becomes singleton → sync value; eliminate the remaining
           digit from every peer (naked single propagation).
        D. After removal, check each unit (row, col, box) for the eliminated
           digit: zero places → contradiction; one place → assign it there
           (hidden single forcing).

        Args:
            board: The board to mutate.
            index: Flat cell index 0-80.
            digit: The digit to remove.

        Returns:
            True on success, False if a contradiction arises.
        """
        cell = board.cells[index]

        # Case A: digit already absent
        if digit not in cell.domain:
            return True

        cell.domain.discard(digit)

        # Case B: domain is now empty → contradiction
        if not cell.domain:
            return False

        # Keep value consistent with domain after every elimination
        cell.sync_value_from_domain()

        # Case C: domain reduced to singleton → propagate naked single
        if len(cell.domain) == 1:
            (remaining,) = cell.domain
            for peer_idx in cell.peers:
                if not ConstraintPropagator.eliminate(board, peer_idx, remaining):
                    return False

        # Case D: check each unit for remaining places for the eliminated digit
        units = [
            board.rows[cell.row],
            board.cols[cell.col],
            board.boxes[cell.box],
        ]
        for unit in units:
            places = [i for i in unit if digit in board.cells[i].domain]
            if len(places) == 0:
                return False  # digit has no home in this unit → contradiction
            if len(places) == 1:
                # hidden single: only one cell in this unit can take digit
                if not ConstraintPropagator.assign(board, places[0], digit):
                    return False

        return True

    @staticmethod
    def initialize(board: Board) -> bool:
        """Re-apply all givens through propagation to reach arc consistency.

        Collects every currently-fixed cell as a given, resets the entire
        board to full domains, then re-assigns each given via ``assign()``
        so that all propagation fires through a single, consistent code path.

        Args:
            board: The board to initialise in-place.

        Returns:
            True if propagation succeeds, False if the puzzle is contradictory.
        """
        givens = [
            (cell.index, next(iter(cell.domain)))
            for cell in board.cells
            if len(cell.domain) == 1
        ]

        # Reset every cell so assign() can propagate from a clean slate
        for cell in board.cells:
            cell.domain = set(range(1, 10))
            cell.value = 0

        for idx, digit in givens:
            if not ConstraintPropagator.assign(board, idx, digit):
                return False

        return True
