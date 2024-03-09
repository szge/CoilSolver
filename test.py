# move

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

# can_move

# >>> cs = CoilSolver()
# >>> cs.boardX = 3
# >>> cs.boardY = 3
# >>> tempboard = np.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
# >>> cs.can_move(tempboard, 1, 0)
# ['D', 'R']

# flood_fill

# >>> cs = CoilSolver()
# >>> cs.boardX = 3
# >>> cs.boardY = 3
# >>> tempboard = np.array([[1, 0, 0],  [0, 1, 0], [0, 0, 1]], int)
# >>> cs.flood_fill(tempboard, 2, 0)
# >>> print(tempboard)
# [[1 1 1]
#  [0 1 1]
#  [0 0 1]]

# solve_board_recursion

# >>> cs = CoilSolver()
# >>> cs.boardX = 3
# >>> cs.boardY = 3
# >>> tempboard = np.array([[1, 0, 0],[0, 0, 0],[0, 0, 1]], int)
# >>> cs.solve_board_recursion(tempboard, 1, 0, "")
# True, 'RDLDR'