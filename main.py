"""Entry point: solve a sample Sudoku puzzle with the ACO solver."""

from aco.solver import SudokuACOSolver

PUZZLE = (
    "53..7...."
    "6..195..."
    ".98....6."
    "8...6...3"
    "4..8.3..1"
    "7...2...6"
    ".6....28."
    "...419..5"
    "....8..79"
)

solver = SudokuACOSolver()
board = solver.solve(PUZZLE)

print(board)
print(f"Solved: {board.is_solved()}")
print(f"History length: {len(solver.history)}")
