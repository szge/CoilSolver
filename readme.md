# Mortal Coil Solver

This is a program that automatically solves [Mortal Coil](http://www.hacker.org/coil/).

Mortal Coil is a grid-based game where the objective is to cover every square. You may start on any open cell and moves
are made in straight lines.

## Setup

Create a `login.txt` file in the same directory as `main.py` with your username on the first line and your password on 
the second line.

`pip install -r requirements.txt`

Then run `main.py`.

## Analysis
An analysis of solve times with different code configurations can be found
[here](https://docs.google.com/spreadsheets/d/1haVOjHmv1FbwTe6wuaShBAYTH-FWUpRFSENnQx9egyU/edit?usp=sharing).

Summary of results:
- The flood fill efficiency is basically operating a flood fill on any open square next to where the current position
lands after a move. If any flood fill does not cover every square then it is impossible for the board to be solved from
the given state. I initially thought this was quite a costly procedure so I initially implemented it such that it would
only check X% of the time, but through experimentation I found that it was actually more efficient to just run it every
time.
- Jeffrey's C++ implementation with the same efficiencies was about 10-30% faster due to being written in C++ but as
expected only yielded a linear scaling of the times, which does not yield much benefit for solving higher levels.
- As expected, adding more efficiencies and checks means it takes longer for trivial levels but it vastly reduces time
taken for the higher levels.
- Progressing further will be more efficient by first reducing sample space than trying to make the code itself cleaner
and more efficient, as this usually only leads to a linear time reduction.


## Manifest
`main.py`: the main part of the program with all the code that is used

`unused.py`: unused code that is in a separate file to prevent clutter