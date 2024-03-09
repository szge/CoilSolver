from __future__ import annotations
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
from typing import List


class CoilSolver:
    username: str = "username"
    password: str = "password"

    def __init__(self):
        # get username and password from login.txt
        with open("login.txt", "r") as file:
            self.username = file.readline().strip()
            self.password = file.readline().strip()

    def solve(self):
        board = self.get_board()
        print(board)
        self.solve_board(board)

    def get_board(self) -> np.ndarray[int] | None:
        url: str = "http://www.hacker.org/coil/index.php?name=" + self.username + "&password=" + self.password
        response = requests.get(url)
        if response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', string=re.compile('boardStr'))
                game_board_str = re.search(r'boardStr = "(.+?)"', script_tag.string).group(1)
                width = int(re.search(r'width = (\d+)', script_tag.string).group(1))
                height = int(re.search(r'height = (\d+)', script_tag.string).group(1))
                board = np.zeros((height, width), dtype=int)
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

        self.submit_solution(0, 0, "")

    def solve_board_recursion(self, board: np.ndarray[int], x: int, y: int, path: str) -> tuple[bool, str]:
        """Given a board and path, it will return (False, "") if the path does not lead to a solution,
        else return [True, <PATH>] with the correct path

        :param board: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param path: the current path
        :return whether the path was successful, and the path it took e.g. "RDLDRU"

        # >>> cs = CoilSolver()
        # >>> tempboard = numpy.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # TODO: Fix this test
        """

        # if there are multiple cells with only one neighbor then it is impossible to solve
        # if self.count_single_avoid_position(tempboard, x, y) >= 2:
        #     return [False, ""]

        valid_dirs: [str] = self.can_move(board, x, y)
        # print("valid dirs", valid_dirs)

        # if len(valid_dirs) > 0:
        #     # Adds flood fill efficiency; if the board is unsolvable then halt recursion.
        #     if self.flood_fill_check(tempboard, x, y, valid_dirs[0]) is False:
        #         return [False, ""]

        for dirs in valid_dirs:
            newboard = board.copy()
            result = self.move(newboard, x, y, dirs)

            if self.check_solved(newboard):
                return True, path + dirs

            succ, new_path = self.solve_board_recursion(newboard, result[0], result[1], path + dirs) # recurse
            if succ:
                return succ, new_path

        return False, ""

    def check_solved(self, board: np.ndarray[int]) -> bool:
        return np.all(board == 1)

    def can_move(self, board: np.ndarray, x: int, y: int) -> List[str]:
        """Finds the directions in which the player can move

        :param board: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return: str array that represents where valid moves are

        # >>> cs = CoilSolver()
        # >>> tempboard = numpy.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
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

    def move(self, board: np.ndarray, x: int, y: int, direction: str) -> (int, int, np.ndarray):
        """Determines how a move affects the state of the board. This mutates tempboard.

        :param board: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param direction: the direction to be moved, either "U", "D", "L", "R"
        :return: List[0]: the x-value of the position after the move
        List[1]: the y-value of the position after the move

        # >>> cs = CoilSolver()
        # >>> tempboard = numpy.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
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

    def submit_solution(self, start_x: int, start_y: int, solution: str):
        url: str = ("http://www.hacker.org/coil/index.php?name=" + self.username + "&password=" + self.password
                    + "&x=" + str(start_x) + "&y=" + str(start_y) + "&path=" + solution)
        # response = requests.post(url, data={"x": start_x, "y": start_y, "path": solution})
        response = requests.get(url)
        if response.status_code == 200:
            pass
        else:
            print("There was an error submitting the solution.")


if __name__ == "__main__":
    cs = CoilSolver()
    while True:
        cs.solve()
        # break
