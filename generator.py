from dokusan import generators

def generate_puzzle(difficulty="medium"):
    ranks = {
        "easy": 30,
        "medium": 50,
        "hard": 100
    }

    avg_rank = ranks.get(difficulty, 50)

    puzzle = str(generators.random_sudoku(avg_rank=avg_rank))
    puzzle = puzzle.replace("0", ".")

    return puzzle