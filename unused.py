# unused code
import numpy


def count_row_empty(self, board: numpy.ndarray, y: int) -> int:
    """Count the amount of empty cells in row <y> of the board"""
    count = 0
    for x in range(self.boardX):
        if board[y][x] == 0:
            count += 1
    return count


def count_col_empty(self, board: numpy.ndarray, x: int) -> int:
    """Count the amount of empty cells in column <x> of the board"""
    count = 0
    for y in range(self.boardY):
        if board[y][x] == 0:
            count += 1
    return count


def row_is_full(self, board: numpy.ndarray, y: int) -> bool:
    """Returns true iff the row <y> of the board is full"""
    for x in range(self.boardX):
        if board[y][x] == 0:
            return False
    return True


def col_is_full(self, board: numpy.ndarray, x: int) -> bool:
    """Returns true iff the row <x> of the board is full"""
    for y in range(self.boardY):
        if board[y][x] == 0:
            return False
    return True

# The following code used to belong in the recursion for loop:
# If a move causes an entire row or col to be filled and there are adjacent empty cells on both sides, halt
# if (direction == "U" or direction == "D") and self.col_is_full(newboard, result[0]):
#     # check if the adjacent columns have any empty squares
#     if result[0] == 0 or self.col_is_full(newboard, result[0] - 1):
#         if result[0] == self.boardX - 1 or self.col_is_full(newboard, result[0] + 1):
#             return [False, ""]
#
# if (direction == "L" or direction == "R") and self.row_is_full(newboard, result[1]):
#     if result[1] == 0 or self.row_is_full(newboard, result[1] - 1):
#         if result[1] == self.boardY - 1 or self.row_is_full(newboard, result[1] + 1):
#             return [False, ""]
