from multiprocessing import Pool
from typing import Tuple

import numpy
"""Resources:
https://stackoverflow.com/questions/20190668/multiprocessing-a-for-loop
https://cuyu.github.io/python/2016/08/15/Terminate-multiprocess-in-Python-correctly-and-gracefully
"""

class CoilSolver:
    # test the alg starting level 1
    # url = "http://www.hacker.org/coil/index.php?"
    boardX: int  # number of columns
    boardY: int  # number of rows
    board: numpy.ndarray  # this is a 2d array representing the board -- 1 for block, else 0s
    level: int  # the current level

    def solve_board(self) -> None:
        """Applies some algorithm to <board> and attempts to solve it.
        """
        succ_path: str = ""
        succ_x: int = 0
        succ_y: int = 0

        for y in range(self.boardY):
            for x in range(self.boardX):
                if self.board[y][x] == 0:
                    thing = self.solve_board_recursion(self.board, x, y, "")
                    # whether or not a successful path has been found
                    if thing[0]:
                        # the actual path
                        succ_path = thing[1]
                        succ_x = x
                        succ_y = y
                        break
            if succ_path != "":
                break

    def solve_board_recursion(self, tempboard: numpy.ndarray, x: int, y: int, path: str) -> Tuple[bool, str]:
        if x == 3 and y == 5:
            return Tuple[True, "RLDU"]
        else:
            return Tuple[False, ""]
