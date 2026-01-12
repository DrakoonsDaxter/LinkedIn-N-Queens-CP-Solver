from pathlib import Path

import pychoco as pc
import visuals as vis
from tqdm import tqdm

def get_puzzle_size(puzzle):
    """Calculates the size n of the n x n puzzle."""
    if isinstance(puzzle, str):
        return len([ln for ln in puzzle.strip().splitlines() if ln.strip()])
    return len(puzzle)

def get_puzzle_regions(puzzle_matrix):
    """Extracts regions from the puzzle matrix. Returns a dict mapping region value to list of (row, col) tuples."""
    regions = {}
    for r, row in enumerate(puzzle_matrix):
        for c, val in enumerate(row):
            if val not in regions:
                regions[val] = []
            regions[val].append((r, c))
    return regions

def write_board_to_txt(board_rows, output_path: Path):
    """
    Writes the board representation to a text file.

    :param board_rows: list of list of str representing the board
    :param output_path: Path to the output text file
    """
    with output_path.open("w") as f:
        for row in board_rows:
            f.write(",".join(str(cell) for cell in row) + "\n")

def solve_puzzle(puzzle_text_path: Path = None, puzzle_matrix = None) -> dict:
    """
    Solve the Linked In Queens puzzle given either a text file path or a matrix representation.
    Returns a dictionary with the number of solutions found, the initial board, and the positions of the queens.

    :param puzzle_text_path: Path to the text file containing the puzzle representation
    :param puzzle_matrix: Matrix representation of the puzzle
    :return: dict with keys "number_of_solutions", "initial_board", "queens"
    """

    if puzzle_text_path is None and puzzle_matrix is None:
        raise ValueError("Either puzzle_text_path or puzzle_matrix must be provided.")
    if puzzle_matrix is not None:
        puzzle = puzzle_matrix
    else:
        puzzle = vis.parse_board_from_txt(puzzle_text_path)

    n = get_puzzle_size(puzzle)
    regions = get_puzzle_regions(puzzle)

    # Solve the puzzle using PyChoco
    model = pc.Model()

    ## Vars
    queen_col = model.intvars(n, 0, n-1)

    # Boolean cell matrix indicating if a queen is at (r, c)
    cell_has_queen = [[model.boolvar() for _ in range(n)] for _ in range(n)]

    # Mapping queen positions to cell matrix
    for r in range(n):
        for c in range(n):
            model.arithm(queen_col[r], "=", c).reify_with(cell_has_queen[r][c])

    ## Linkedin Queens Rules

    # 1) Only one queen per column and per line
    model.all_different(queen_col).post()

    # 2) There can't be Queens at cell distance 1 from each other
    for i in range(n - 1):
        model.distance(queen_col[i], queen_col[i+1], ">", 1).post()

    # 3) Each region should have exactly one queen
    for region_cells in regions.values():
        model.sum([cell_has_queen[r][c] for r, c in region_cells], "=", 1).post()
    
    solver = model.get_solver()

    # first solution
    solver.solve()
    first_solution = [(r, queen_col[r].get_value()) for r in range(n)]

    # count other solutions
    count = 1
    while solver.solve():
        count += 1

    return {
        "number_of_solutions": count,
        "initial_board" : puzzle,
        "queens" : first_solution
    }

def single_puzzle_solve(puzzle_text_path: Path, output_image_path: Path, output_text_path: Path, save: bool = True, verbose: bool = False):
    """
    Solve a single puzzle given its text file path, and save/display the solution.
    
    :param puzzle_text_path: Path to the text file containing the puzzle representation
    :param output_image_path: Path to save the output image
    :param output_text_path: Path to save the output text file
    """

    # Solve the puzzle
    solution = solve_puzzle(puzzle_text_path)

    # Extract initial board and queen positions from the solution
    initial_board = solution['initial_board']
    queens = solution['queens']  # List of (row, col) tuples
    number_of_solutions = solution['number_of_solutions']

    if number_of_solutions != 1:
        print(f"Warning: Puzzle {puzzle_text_path.name} has {number_of_solutions} solutions.")

    if verbose:
        print(f"Puzzle: {puzzle_text_path.name} - Number of solutions found: {number_of_solutions}")

    # Save and display the solution
    if save:
        save_and_display_solution(initial_board, queens, output_image_path=output_image_path, output_text_path=output_text_path, save_image=True, display=False)

def all_puzzles_solve(puzzles_dir: Path, output_image_path: Path, output_text_path: Path, save: bool = True, verbose: bool = False):
    """
    Solve all puzzles in a directory, saving and optionally displaying their solutions.
    
    :param puzzles_dir: Directory containing puzzle text files
    :param output_image_path: Directory to save output images
    :param output_text_path: Directory to save output text files
    :param verbose: Whether to print progress information
    """
    puzzle_files = sorted(puzzles_dir.glob("*.txt"))
    
    for puzzle_file in tqdm(puzzle_files, desc="Solving puzzles", unit="puzzle"):
        single_puzzle_solve(
            puzzle_file, 
            output_image_path / f"{puzzle_file.stem}.png", 
            output_text_path=output_text_path / f"{puzzle_file.stem}.txt", 
            save=save,
            verbose=verbose
        )

def save_and_display_solution(initial_board, queens, output_text_path: str = "./outputs/solution.txt", output_image_path: str = "./outputs/solution.png", save_text=True, save_image=True, display=False):
    """
    initial_board: Matrix repesenting the initial board configuration
    queens: list of (row, col) tuples where queens are placed
    output_path: Path to save the output image
    save_image: Whether to save the image
    display: Whether to display the image
    """

    # Create a copy of the initial board
    board_rows = [row[:] for row in initial_board]

    # Place queens on the board
    for r, c in queens:
        board_rows[r][c] = "Q" + str(board_rows[r][c])

    # Generate and save/display the board visuals
    vis.generate_board_visuals(board_rows, output_path=vis.Path(output_image_path), save_image=save_image, display=display)
    write_board_to_txt(board_rows, vis.Path(output_text_path))

if __name__ == "__main__":
    
    # Output dir
    OUTPUT_DIR = Path("./outputs")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Execution:
    INPUT_DIR = Path("./puzzles/puzzle_text/problems") # Directory containing the problem text files

    save = False
    measure_time = True

    if measure_time:
        import time
        start_time = time.time()

    # 1) Single Puzzle Execution
    PUZZLE_NUMBER = 170 # from 170 to 534
    PUZZLE_PATH = INPUT_DIR / f"{PUZZLE_NUMBER}.txt"
    #single_puzzle_solve(PUZZLE_PATH, output_image_path=OUTPUT_DIR / f"{PUZZLE_NUMBER}.png", output_text_path=OUTPUT_DIR / f"{PUZZLE_NUMBER}.txt", save=save, verbose=True)

    # 2) All Puzzle Execution
    SIZE_N = 4
    PUZZLE_DIR = INPUT_DIR / f"{SIZE_N}x{SIZE_N}"
    all_puzzles_solve(PUZZLE_DIR, output_image_path=OUTPUT_DIR, output_text_path=OUTPUT_DIR, save=save, verbose=False)

    if measure_time:
        end_time = time.time()
        print(f"Total execution time: {end_time - start_time:.2f} seconds")

