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
        self.solve_board(board)
        # self.solve_board_parallel(board)
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
        """Given a board and path, it will return [False, ""] if the path does not lead to a solution or it will return
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

        for dir in valid_dirs:
            newboard = board.copy()
            x_new, y_new, board_new, needs_flood_check = self.move(newboard, x, y, dir)

            if self.check_solved(newboard):
                return True, path + dir

            if needs_flood_check and not self.flood_check(board_new, x_new, y_new):
                return False, ""

            succ, full_path = self.solve_board_recursion(newboard, x_new, y_new, path + dir)  # recurse
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
            if abs(curr_y - y) + abs(curr_x - x) > 1 and self.count_num_empty_neighbors(board, x, y) == 1:
                single_empty_neighbors += 1
                if single_empty_neighbors > 1:
                    return False
        return True

    def count_num_empty_neighbors(self, board: np.ndarray[int], x: int, y: int) -> int:
        rows, cols = board.shape
        count = 0
        if y > 0 and board[y - 1][x] == 0:
            count += 1
        if y < rows - 1 and board[y + 1][x] == 0:
            count += 1
        if x > 0 and board[y][x - 1] == 0:
            count += 1
        if x < cols - 1 and board[y][x + 1] == 0:
            count += 1
        return count

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
        for dir in dirs:
            checkboard = board.copy()
            if dir == "U":
                self.flood_fill(checkboard, x, y - 1)
            elif dir == "D":
                self.flood_fill(checkboard, x, y + 1)
            elif dir == "L":
                self.flood_fill(checkboard, x - 1, y)
            elif dir == "R":
                self.flood_fill(checkboard, x + 1, y)
            # if not self.check_solved(checkboard):
            #     return False
        return True

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

    def check_solved(self, board: np.ndarray[int]) -> bool:
        return np.all(board == 1)

    def legal_moves(self, board: np.ndarray, x: int, y: int) -> List[str]:
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
        :return: (new_x, new_y, new_board)
        """

        board[y][x] = 1
        rows, cols = board.shape
        needs_flood_check = False
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

        while self.is_valid_move(board, x, y, direction):
            x += dx
            y += dy
            board[y][x] = 1

        # if direction == "U":
        #     emptyL = x > 0 and board[y][x - 1] == 0
        #     emptyR = x < cols - 1 and board[y][x + 1] == 0
        #     while y > 0 and board[y - 1][x] == 0:
        #         y -= 1
        #         board[y][x] = 1
        #         emptyL = emptyL or (x > 0 and board[y][x - 1] == 0)
        #         emptyR = emptyR or (x < cols - 1 and board[y][x + 1] == 0)
        #     needs_flood_check = (emptyL and emptyR)
        # elif direction == "D":
        #     emptyL = x > 0 and board[y][x - 1] == 0
        #     emptyR = x < cols - 1 and board[y][x + 1] == 0
        #     while y < rows - 1 and board[y + 1][x] == 0:
        #         y += 1
        #         board[y][x] = 1
        #         emptyL = emptyL or (x > 0 and board[y][x - 1] == 0)
        #         emptyR = emptyR or (x < cols - 1 and board[y][x + 1] == 0)
        #     needs_flood_check = (emptyL and emptyR)
        # elif direction == "L":
        #     emptyU = y > 0 and board[y - 1][x] == 0
        #     emptyD = y < rows - 1 and board[y + 1][x] == 0
        #     while x > 0 and board[y][x - 1] == 0:
        #         x -= 1
        #         board[y][x] = 1
        #         emptyU = emptyU or (y > 0 and board[y - 1][x] == 0)
        #         emptyD = emptyD or (y < rows - 1 and board[y + 1][x] == 0)
        #     needs_flood_check = (emptyU and emptyD)
        # elif direction == "R":
        #     emptyU = y > 0 and board[y - 1][x] == 0
        #     emptyD = y < rows - 1 and board[y + 1][x] == 0
        #     while x < cols - 1 and board[y][x + 1] == 0:
        #         x += 1
        #         board[y][x] = 1
        #         emptyU = emptyU or (y > 0 and board[y - 1][x] == 0)
        #         emptyD = emptyD or (y < rows - 1 and board[y + 1][x] == 0)
        #     needs_flood_check = (emptyU and emptyD)
        # else:
        #     print("An invalid direction was submitted to the move function")

        return x, y, board, True

    def is_valid_move(self, board: np.ndarray[int], x: int, y: int, dir: str) -> bool:
        if dir == "U" and y > 0 and board[y - 1][x] == 0:
            return True
        if dir == "D" and y < board.shape[0] - 1 and board[y + 1][x] == 0:
            return True
        if dir == "L" and x > 0 and board[y][x - 1] == 0:
            return True
        if dir == "R" and x < board.shape[1] - 1 and board[y][x + 1] == 0:
            return True
        return False


if __name__ == "__main__":
    cs = CoilSolver()
    while True:
        cs.solve()
