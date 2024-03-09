from __future__ import annotations
from typing import List, Union
import time
import numpy
import requests
from bs4 import BeautifulSoup
import re

"""Resources:
http://www.hacker.org/forum/viewtopic.php?t=1093
https://docs.google.com/spreadsheets/d/1haVOjHmv1FbwTe6wuaShBAYTH-FWUpRFSENnQx9egyU/edit?usp=sharing

"""


class CoilSolver:
    username: str = "username"
    password: str = "password"
    url: str = "http://www.hacker.org/coil/index.php?name=" + username + "&password=" + password
    boardX: int  # Number of columns
    boardY: int  # Number of rows
    board: numpy.ndarray  # 2D array representing the board -- 1 for block, else 0s
    timer_start: float = time.perf_counter()  # Timer start time for each level computation
    level: int  # The current level number

    def __init__(self):
        with open("login.txt", "r") as file:
            self.username = file.readline().strip()
            self.password = file.readline().strip()

    def parse_board(self) -> numpy.ndarray[int] | None:
        url: str = "http://www.hacker.org/coil?name=" + self.username + "&password=" + self.password
        response = requests.get(url)
        if response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', string=re.compile('boardStr'))
                game_board_str = re.search(r'boardStr = "(.+?)"', script_tag.string).group(1)
                width = int(re.search(r'width = (\d+)', script_tag.string).group(1))
                height = int(re.search(r'height = (\d+)', script_tag.string).group(1))
                board = numpy.zeros((height, width), dtype=int)
                for i, char in enumerate(game_board_str):
                    row, col = i // width, i % width
                    if char == 'X':
                        board[row, col] = 1
                self.board = board
                self.boardX = width
                self.boardY = height
                return board
            except Exception as e:
                print("There was an error parsing the page.", e)
                print(response.text)
                return None
        else:
            print("There was an error loading the page.")
            return None

    def solve_board(self) -> None:
        """Applies some algorithm to <board> and attempts to solve it.
        """
        succ_path: str = ""
        succ_x: int = 0
        succ_y: int = 0

        print(self.board)

        for y in range(self.boardY):
            for x in range(self.boardX):
                if self.board[y][x] == 0:
                    thing = self.solve_board_recursion(self.board, x, y, "")
                    if thing[0]:
                        # the actual path
                        succ_path = thing[1]
                        succ_x = x
                        succ_y = y
                        break
            if succ_path != "":
                break

        print(succ_x, succ_y, succ_path)

        response = requests.get(self.url + "&x=" + str(succ_x) + "&y=" + str(succ_y) + "&path=" + succ_path)
        if response.status_code == 200:
            self.parse_board()
            self.solve_board()
        else:
            print("There was an error loading the page.")

    def solve_board_recursion(self, tempboard: numpy.ndarray, x: int, y: int, path: str) -> List[Union[bool, str]]:
        """Given a board and path, it will return [False, ""] if the path does not lead to a solution or it will return
        [True, <PATH>] with the correct path

        :param tempboard: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param path: the current path
        :return List[0]: whether or not the path was successful, True = succ
        List[1]: if a path is successful, the path it took e.g. "RDLDRU"

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = numpy.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # >>> cs.solve_board_recursion(tempboard, 1, 0, "")
        # [True, 'RDLDR']
        """

        # if there are multiple cells with only one neighbor then it is impossible to solve
        if self.count_single_avoid_position(tempboard, x, y) >= 2:
            return [False, ""]

        valid_directions: [bool] = self.can_move(tempboard, x, y)

        if len(valid_directions) > 0:
            # Adds flood fill efficiency; if the board is unsolvable then halt recursion.
            if self.flood_fill_check(tempboard, x, y, valid_directions[0]) is False:
                return [False, ""]

        for direction in valid_directions:
            # Move in a given direction
            newboard = tempboard.copy()
            result = self.move(newboard, x, y, direction)

            # Check for solve
            if self.check_solved(newboard):
                return [True, path + direction]

            # Recursive case when board is not solved
            thing = self.solve_board_recursion(newboard, result[0], result[1], path + direction)
            if thing[0]:
                return thing

        return [False, ""]

    def count_single_avoid_position(self, board: numpy.ndarray, x, y) -> int:
        """Count the number of free single free neighbor cells in a grid, ignoring the neighbors of the current
        position at (<x>, <y>). It's fine if the neighboring cells around the current position are single since we can
        go there so they should be ignored. Does not mutate board.

        """
        newboard = self.create_connections_grid(board)

        single_count = 0
        for y_count in range(self.boardY):
            for x_count in range(self.boardX):
                # It's fine if the neighboring cells around the current position are single since we can go there
                # normally so I should avoid checking them
                if abs(y_count - y) + abs(x_count - x) > 1 and newboard[y_count][x_count] == 1:
                    single_count += 1
        return single_count

    def create_connections_grid(self, board: numpy.ndarray) -> numpy.ndarray:
        """Returns a grid such that each corresponding empty cell counts how many neighboring cells are empty.
        Already filled blocks are ignored (value of zero). Does not mutate board.
        :param board:
        :return:

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 4
        # >>> cs.boardY = 3
        # >>> tempboard = numpy.array([[1, 0, 0, 0],  [0, 1, 0, 0], [0, 0, 1, 0]], int)
        # >>> print(cs.create_connections_grid(tempboard))
        # [[0 1 3 2]
        #  [1 0 2 3]
        #  [2 1 0 1]]
        """
        tempboard = numpy.zeros((self.boardY, self.boardX), dtype=int)
        for y in range(self.boardY):
            for x in range(self.boardX):
                if board[y][x] == 0:
                    if y > 0 and board[y - 1][x] == 0:
                        tempboard[y][x] += 1
                    if y < self.boardY - 1 and board[y + 1][x] == 0:
                        tempboard[y][x] += 1
                    if x > 0 and board[y][x - 1] == 0:
                        tempboard[y][x] += 1
                    if x < self.boardX - 1 and board[y][x + 1] == 0:
                        tempboard[y][x] += 1
        return tempboard

    def flood_fill_check(self, tempboard: numpy.ndarray, x: int, y: int, direction: str) -> bool:
        """Uses flood fill starting at a given x, y position to determine if a board is solvable in a given state. If a
        flood fill cannot fill the whole board it means it cannot be solved. Take in a board, returns False if it is not
        solvable. Does not mutate tempboard.

        :param tempboard:
        :param x: current x position
        :param y: current y position
        :param direction:
        :return:
        """
        checkboard = tempboard.copy()

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

    def flood_fill(self, tempboard: numpy.ndarray, x: int, y: int) -> None:
        """Starts flood filling tempboard from a given (<x>, <y>) position.
        Warning: mutates tempboard

        :param tempboard: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return:

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = numpy.array([[1, 0, 0],  [0, 1, 0], [0, 0, 1]], int)
        # >>> cs.flood_fill(tempboard, 2, 0)
        # >>> print(tempboard)
        # [[1 1 1]
        #  [0 1 1]
        #  [0 0 1]]
        """
        if tempboard[y][x] == 0:
            tempboard[y][x] = 1
            # flood fill upwards
            if y > 0:
                self.flood_fill(tempboard, x, y - 1)
            # flood fill downwards
            if y < self.boardY - 1:
                self.flood_fill(tempboard, x, y + 1)
            # flood fill leftwards
            if x > 0:
                self.flood_fill(tempboard, x - 1, y)
            # flood fill rightwards
            if x < self.boardX - 1:
                self.flood_fill(tempboard, x + 1, y)

    def count_board_empty(self, board: numpy.ndarray) -> int:
        """Counts how many empty spaces there are left on the board

        :param board: the current state of the board
        :return:

        # >>> tempboard = numpy.array([[1, 1, 1],[0, 1, 1],[0, 0, 1]], int)
        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> cs.count_board_empty(tempboard)
        # 3
        """
        count = 0
        for y in range(self.boardY):
            for x in range(self.boardX):
                count += board[y][x]
        return self.boardY * self.boardX - count

    def check_solved(self, board) -> bool:
        for y in range(self.boardY):
            for x in range(self.boardX):
                if board[y][x] == 0:
                    return False
        timer_end = time.perf_counter()
        # print("Time for solve: " + str(timer_end - self.timer_start))
        print("%.3f" % (timer_end - self.timer_start))
        self.timer_start = timer_end
        return True

    def can_move(self, tempboard: numpy.ndarray, x: int, y: int) -> List[str]:
        """Finds the directions in which the player can move

        :param tempboard: the board to be checked
        :param x: the current x position on the board
        :param y: the current y position on the board
        :return: str array that represents where valid moves are

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
        # >>> tempboard = numpy.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
        # >>> cs.can_move(tempboard, 1, 0)
        # ['D', 'R']
        """
        arr = []

        # check if you can move up
        if y > 0 and tempboard[y - 1][x] == 0:
            arr.append("U")
        # check if you can move down
        if y < self.boardY - 1 and tempboard[y + 1][x] == 0:
            arr.append("D")
        # check if you can move left
        if x > 0 and tempboard[y][x - 1] == 0:
            arr.append("L")
        # check if you can move right
        if x < self.boardX - 1 and tempboard[y][x + 1] == 0:
            arr.append("R")
        return arr

    def move(self, tempboard: numpy.ndarray, x: int, y: int, direction: str) -> List[Union[int, int, numpy.ndarray]]:
        """Determines how a move affects the state of the board. This mutates tempboard.

        :param tempboard: the current state of the board
        :param x: the current position's x value
        :param y: the current position's y value
        :param direction: the direction to be moved, either "U", "D", "L", "R"
        :return: List[0]: the x-value of the position after the move
        List[1]: the y-value of the position after the move

        # >>> cs = CoilSolver()
        # >>> cs.boardX = 3
        # >>> cs.boardY = 3
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

        tempboard[y][x] = 1

        if direction == "U":
            while y > 0 and tempboard[y - 1][x] == 0:
                tempboard[y - 1][x] = 1
                y -= 1
        elif direction == "D":
            while y < self.boardY - 1 and tempboard[y + 1][x] == 0:
                tempboard[y + 1][x] = 1
                y += 1
        elif direction == "L":
            while x > 0 and tempboard[y][x - 1] == 0:
                tempboard[y][x - 1] = 1
                x -= 1
        elif direction == "R":
            while x < self.boardX - 1 and tempboard[y][x + 1] == 0:
                tempboard[y][x + 1] = 1
                x += 1
        else:
            print("An invalid direction was submitted to the move function")

        return [x, y, tempboard]

    def main(self) -> None:
        response = requests.get(self.url)
        if response.status_code == 200:
            self.parse_board()
            self.solve_board()
        else:
            print("There was an error loading the page.")


if __name__ == "__main__":
    # import doctest
    # doctest.testmod()

    cs = CoilSolver()
    cs.main()