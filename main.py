from typing import List, Union
import time
import numpy as np
import requests
from bs4 import BeautifulSoup
import re


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
        print("Time to solve: %.3fs" % (time.perf_counter() - self.timer_start))

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
        for y in range(board.shape[0]):
            for x in range(board.shape[1]):
                if board[y, x] == 0:
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
        :return List[0]: whether the path was successful, True = succ
        List[1]: if a path is successful, the path it took e.g. "RDLDRU"

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = np.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # >>> cs.solve_board_recursion(tempboard, 1, 0, "")
        # True, 'RDLDR'
        """

        if not self.neighbors_valid(board, x, y):
            return False, ""

        valid_dirs = self.can_move(board, x, y)

        if len(valid_dirs) > 0:
            if self.flood_fill_check(board, x, y, valid_dirs[0]) is False:
                return False, ""

        for dirs in valid_dirs:
            newboard = board.copy()
            result = self.move(newboard, x, y, dirs)

            if self.check_solved(newboard):
                return True, path + dirs

            thing = self.solve_board_recursion(newboard, result[0], result[1], path + dirs)  # recurse
            if thing[0]:
                return thing

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
        rows, cols = board.shape
        single_empty_neighbors = 0
        for y in range(rows):
            for x in range(cols):
                if board[y, x] == 0 and abs(curr_y - y) + abs(curr_x - x) > 1:
                    if self.count_num_empty_neighbors(board, x, y) == 1:
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

    def flood_fill_check(self, board: np.ndarray, x: int, y: int, direction: str) -> bool:
        """Uses flood fill starting at a given x, y position to determine if a board is solvable in a given state. If a
        flood fill cannot fill the whole board it means it cannot be solved. Take in a board, returns False if it is not
        solvable. Does not mutate tempboard.

        :param board:
        :param x: current x position
        :param y: current y position
        :param direction:
        :return:
        """
        checkboard = board.copy()

        if direction == "U":
            self.flood_fill(checkboard, x, y - 1)
        elif direction == "D":
            self.flood_fill(checkboard, x, y + 1)
        elif direction == "L":
            self.flood_fill(checkboard, x - 1, y)
        elif direction == "R":
            self.flood_fill(checkboard, x + 1, y)
        if self.count_board_empty(checkboard) > 0:
            return False
        return True

    def flood_fill(self, tempboard: np.ndarray, x: int, y: int) -> None:
        """Starts flood filling tempboard from a given (<x>, <y>) position.
        Warning: mutates tempboard

        :param tempboard: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return:

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = np.array([[1, 0, 0],  [0, 1, 0], [0, 0, 1]], int)
        # >>> cs.flood_fill(tempboard, 2, 0)
        # >>> print(tempboard)
        # [[1 1 1]
        #  [0 1 1]
        #  [0 0 1]]
        """
        rows, cols = tempboard.shape
        if tempboard[y][x] == 0:
            tempboard[y][x] = 1
            # flood fill upwards
            if y > 0:
                self.flood_fill(tempboard, x, y - 1)
            # flood fill downwards
            if y < rows - 1:
                self.flood_fill(tempboard, x, y + 1)
            # flood fill leftwards
            if x > 0:
                self.flood_fill(tempboard, x - 1, y)
            # flood fill rightwards
            if x < cols - 1:
                self.flood_fill(tempboard, x + 1, y)

    def count_board_empty(self, board: np.ndarray) -> int:
        """Counts how many empty spaces there are left on the board

        :param board: the current state of the board
        :return:

        # >>> tempboard = np.array([[1, 1, 1],[0, 1, 1],[0, 0, 1]], int)
        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> cs.count_board_empty(tempboard)
        # 3
        """
        rows, cols = board.shape
        count = 0
        for y in range(rows):
            for x in range(cols):
                count += board[y][x]
        return rows * cols - count

    def check_solved(self, board: np.ndarray[int]) -> bool:
        return np.all(board == 1)

    def can_move(self, board: np.ndarray, x: int, y: int) -> List[str]:
        """Finds the directions in which the player can move

        :param board: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return: str array that represents where valid moves are

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = np.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # >>> cs.can_move(tempboard, 1, 0)
        # ['D', 'R']
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

    def move(self, board: np.ndarray[int], x: int, y: int, direction: str) -> tuple[int, int, np.ndarray[int]]:
        """Determines how a move affects the state of the board. This mutates tempboard.

        :param board: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param direction: the direction to be moved, either "U", "D", "L", "R"
        :return: List[0]: the x-value of the position after the move
        List[1]: the y-value of the position after the move

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = np.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # >>> output = cs.move(tempboard, 1, 0, "D")
        # >>> output[0]
        # 1
        # >>> output[1]
        # 2
        # >>> print(output[2])
        # [[1 1 0]
        #  [0 1 0]
        #  [0 1 1]]
        """

        board[y][x] = 1
        rows, cols = board.shape

        if direction == "U":
            while y > 0 and board[y - 1][x] == 0:
                board[y - 1][x] = 1
                y -= 1
        elif direction == "D":
            while y < rows - 1 and board[y + 1][x] == 0:
                board[y + 1][x] = 1
                y += 1
        elif direction == "L":
            while x > 0 and board[y][x - 1] == 0:
                board[y][x - 1] = 1
                x -= 1
        elif direction == "R":
            while x < cols - 1 and board[y][x + 1] == 0:
                board[y][x + 1] = 1
                x += 1
        else:
            print("An invalid direction was submitted to the move function")

        return x, y, board


if __name__ == "__main__":
    # import doctest
    # doctest.testmod()

    cs = CoilSolver()
    while True:
        cs.solve()
