from dokusan import generators


def generate_puzzle(difficulty: str = "medium") -> str:
    """
    Generate a Sudoku puzzle string at the requested difficulty level.

    Supported difficulty labels: easy, medium, hard, expert.
    Internally maps each label to a dokusan avg_rank value that controls
    how constrained (harder) the generated puzzle is.

    Returns an 81-character string where digits 1-9 are given cells and
    '.' represents an empty cell.
    """
    difficulty_to_rank = {
        "easy": 30,
        "medium": 50,
        "hard": 100,
        "expert": 200,
    }

    if difficulty not in difficulty_to_rank:
        raise ValueError(
            f"Invalid difficulty '{difficulty}'. Must be one of: easy, medium, hard, expert."
        )

    avg_rank = difficulty_to_rank[difficulty]

    puzzle = str(generators.random_sudoku(avg_rank=avg_rank))
    puzzle = puzzle.replace("0", ".")

    if len(puzzle) != 81 or not all(ch in "123456789." for ch in puzzle):
        raise ValueError("Generated puzzle is invalid.")

    return puzzle
