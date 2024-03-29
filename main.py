from typing import List
import time
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import multiprocessing as mp
from queue import Empty


class CoilSolver:
    username: str = "username"
    password: str = "password"
    timer_start: float = time.perf_counter()  # Timer start time for each level computation

    def __init__(self):
        with open("login.txt", "r") as file:
            self.username = file.readline().strip()
            self.password = file.readline().strip()
    
    def solve(self):
        board = self.get_board()
        print(board)
        self.timer_start = time.perf_counter()
        # self.solve_board(board)
        self.solve_board_parallel(board)
        print("Time to solve: %.3fs" % (time.perf_counter() - self.timer_start))

    def solve_board_parallel(self, board: np.ndarray[int]):
        unchecked_positions = mp.Queue()

        zero_indices = np.transpose(np.nonzero(board == 0))
        for y, x in zero_indices:
            unchecked_positions.put((x, y))

        print(f"Initial queue size: {unchecked_positions.qsize()}")

        solution_found = mp.Value('b', False)  # solution found shared value

        # Create worker processes
        num_processes = mp.cpu_count()
        processes = []
        for _ in range(num_processes):
            p = mp.Process(target=self.worker_solve, args=(board, unchecked_positions, solution_found))
            processes.append(p)
            p.start()

        # Wait for processes to finish
        for p in processes:
            p.join()

        if not solution_found.value:
            print("No solution found.")
            self.submit_solution(0, 0, "")

    def worker_solve(self, board: np.ndarray[int], unchecked_positions: mp.Queue, solution_found: mp.Value):
        while not solution_found.value:
            try:
                x, y = unchecked_positions.get(timeout=1)
                if unchecked_positions.qsize() % 10 == 0:
                    print(f"Remaining queue size: {unchecked_positions.qsize()}")
            except Empty:
                break

            succ, path = self.solve_board_recursion(board, x, y, "")
            if succ:
                solution_found.value = True
                print("Solved!", x, y, path)
                self.submit_solution(x, y, path)
                break

    def get_board(self) -> np.ndarray[int] | None:
        url = "http://www.hacker.org/coil?name=" + self.username + "&password=" + self.password
        response = requests.get(url)
        if response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', string=re.compile('boardStr'))
                game_board_str = re.search(r'boardStr = "(.+?)"', script_tag.string).group(1)
                width = int(re.search(r'width = (\d+)', script_tag.string).group(1))
                height = int(re.search(r'height = (\d+)', script_tag.string).group(1))
                board = np.zeros((height, width), dtype=int)
                level = int(re.search(r'Level: (\d+)', response.text).group(1))
                print(f"Level: {level}, dimensions: {width}x{height}")

                for i, char in enumerate(game_board_str):
                    row, col = i // width, i % width
                    if char == 'X':
                        board[row, col] = 1
                return board
            except Exception as e:
                print("There was an error parsing the page.", e)
                print(response.text)
                return None
        else:
            print("There was an error loading the page.")
            return None

    def solve_board(self, board: np.ndarray[int]):
        zero_indices = np.transpose(np.nonzero(board == 0))
        for y, x in zero_indices:
            succ, path = self.solve_board_recursion(board, x, y, "")
            if succ:
                print("Solved!", x, y, path)
                self.submit_solution(x, y, path)
                return
        print("No solution found.")
        self.submit_solution(0, 0, "")

    def submit_solution(self, start_x: int, start_y: int, solution: str):
        url: str = ("http://www.hacker.org/coil?name=" + self.username + "&password=" + self.password
                    + "&x=" + str(start_x) + "&y=" + str(start_y) + "&path=" + solution)
        # response = requests.post(url, data={"x": start_x, "y": start_y, "path": solution})
        response = requests.get(url)
        if response.status_code == 200:
            pass
        else:
            print("There was an error submitting the solution.")

    def solve_board_recursion(self, board: np.ndarray, x: int, y: int, path: str) -> tuple[bool, str]:
        """Given a board and path, it will return [False, ""] if the path does not lead to a solution, or
        [True, <PATH>] with the correct path

        :param board: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param path: the current path
        :return (succ, full path)
        """
        if not self.neighbors_valid(board, x, y):
            return False, ""

        valid_dirs = self.legal_moves(board, x, y)

        for dirs in valid_dirs:
            newboard = board.copy()
            x_new, y_new, board_new, needs_flood_check = self.move(newboard, x, y, dirs)

            if self.check_solved(newboard):
                return True, path + dirs

            if needs_flood_check and self.flood_check(board_new, x_new, y_new) or not needs_flood_check:
                # recurse only if flood check passes
                succ, full_path = self.solve_board_recursion(newboard, x_new, y_new, path + dirs)
                if succ:
                    return succ, full_path

        return False, ""

    def neighbors_valid(self, board: np.ndarray[int], curr_x: int, curr_y: int) -> bool:
        """
        If an empty cell only has one empty neighbor, it must be the last cell to be filled.
        Ignore neighbors of the current (x, y) cell, since we can reach those.
        :param board:
        :param curr_x:
        :param curr_y:
        :return:
        """
        single_empty_neighbors = 0
        zero_indices = np.transpose(np.nonzero(board == 0))

        for y, x in zero_indices:
            if abs(curr_y - y) + abs(curr_x - x) > 1 and len(self.legal_moves(board, x, y)) == 1:
                single_empty_neighbors += 1
                if single_empty_neighbors > 1:
                    return False
        return True

    def flood_check(self, board: np.ndarray, x: int, y: int) -> bool:
        """If flood fill cannot fill the whole board it cannot be solved.
        You only need check flood fill if by moving there are empty squares on both sides.
        Does not mutate tempboard.

        :param board:
        :param x: current x position
        :param y: current y position
        :return: whether flood fill fills the whole board
        """
        dirs = self.legal_moves(board, x, y)
        solvable = False
        for d in dirs:
            checkboard = board.copy()
            if d == "U":
                self.flood_fill(checkboard, x, y - 1)
            elif d == "D":
                self.flood_fill(checkboard, x, y + 1)
            elif d == "L":
                self.flood_fill(checkboard, x - 1, y)
            elif d == "R":
                self.flood_fill(checkboard, x + 1, y)
            if self.check_solved(checkboard):
                solvable = True
                break
        return solvable

    def flood_fill(self, tempboard: np.ndarray, x: int, y: int) -> None:
        """Starts flood filling tempboard from a given (<x>, <y>) position. Mutates tempboard

        :param tempboard: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return:
        """
        rows, cols = tempboard.shape
        if tempboard[y][x] == 0:
            tempboard[y][x] = 1
            if y > 0:
                self.flood_fill(tempboard, x, y - 1)
            if y < rows - 1:
                self.flood_fill(tempboard, x, y + 1)
            if x > 0:
                self.flood_fill(tempboard, x - 1, y)
            if x < cols - 1:
                self.flood_fill(tempboard, x + 1, y)

    @staticmethod
    def check_solved(board: np.ndarray[int]) -> bool:
        return np.all(board == 1)

    @staticmethod
    def legal_moves(board: np.ndarray, x: int, y: int) -> List[str]:
        """Finds the directions in which the player can move

        :param board: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return: str array that represents where valid moves are
        """
        moves = []
        rows, cols = board.shape

        if y > 0 and board[y - 1][x] == 0:
            moves.append("U")
        if y < rows - 1 and board[y + 1][x] == 0:
            moves.append("D")
        if x > 0 and board[y][x - 1] == 0:
            moves.append("L")
        if x < cols - 1 and board[y][x + 1] == 0:
            moves.append("R")

        return moves

    def move(self, board: np.ndarray[int], x: int, y: int, direction: str) -> tuple[int, int, np.ndarray[int], bool]:
        """Determines how a move affects the state of the board. This mutates tempboard.

        :param board: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param direction: the direction to be moved, either "U", "D", "L", "R"
        :return: (new_x, new_y, new_board, needs_flood_check)
        """

        board[y][x] = 1
        rows, cols = board.shape
        dx, dy = 0, 0
        if direction == "U":
            dy = -1
        elif direction == "D":
            dy = 1
        elif direction == "L":
            dx = -1
        elif direction == "R":
            dx = 1
        else:
            print("An invalid direction was submitted to the move function")

        emptyDir1 = (0 <= y + dx < rows and 0 <= x + dy < cols and board[y + dx][x + dy] == 0)
        emptyDir2 = (0 <= y - dx < rows and 0 <= x - dy < cols and board[y - dx][x - dy] == 0)

        while self.is_valid_move(board, x, y, direction):
            x += dx
            y += dy
            emptyDir1 = (emptyDir1 or (0 <= y + dx < rows and 0 <= x + dy < cols and board[y + dx][x + dy] == 0))
            emptyDir2 = (emptyDir2 or (0 <= y - dx < rows and 0 <= x - dy < cols and board[y - dx][x - dy] == 0))
            board[y][x] = 1

        return x, y, board, emptyDir1 and emptyDir2

    @staticmethod
    def is_valid_move(board: np.ndarray[int], x: int, y: int, direction: str) -> bool:
        if direction == "U" and y > 0 and board[y - 1][x] == 0:
            return True
        if direction == "D" and y < board.shape[0] - 1 and board[y + 1][x] == 0:
            return True
        if direction == "L" and x > 0 and board[y][x - 1] == 0:
            return True
        if direction == "R" and x < board.shape[1] - 1 and board[y][x + 1] == 0:
            return True
        return False


if __name__ == "__main__":
    cs = CoilSolver()
    while True:
        cs.solve()
