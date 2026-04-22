"""Entry point: solve a sample Sudoku puzzle with the ACO solver."""

from aco.solver import SudokuACOSolver

from generator import generate_puzzle
PUZZLE = generate_puzzle("medium")

#print raw puzzle
print("Generated puzzle:")
for i in range(0, 81, 9):
    print(PUZZLE[i:i+9])

solver = SudokuACOSolver()
board = solver.solve(PUZZLE)

print(board)
print(f"Solved: {board.is_solved()}")
print(f"History length: {len(solver.history)}")
