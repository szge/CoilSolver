# Mortal Coil Solver

This is a program that automatically solves [Mortal Coil](http://www.hacker.org/coil/).
To run it, simply run the main method in main.py.

Mortal Coil is a grid-based game where the objective is to cover every square. You may start on any open cell and moves
are made in straight lines.

## Configuration

In the `CoilSolver` class, replace the `username` and `password` fields with the details of your account.

## Troubleshooting
There are a few `print` statements throughout the code that you may uncomment to provide more information.
Currently, the only output is the time in seconds required to solve each level. This is to make it easier to copy and
paste into spreadsheet programs.

If there is a network issue, the code should print an error message and halt execution.

## Analysis
An analysis of solve times with different code configurations can be found
[here](https://docs.google.com/spreadsheets/d/1haVOjHmv1FbwTe6wuaShBAYTH-FWUpRFSENnQx9egyU/edit?usp=sharing).

## Manifest
`main.py`: the main part of the program with all the code that is used

`unused.py`: unused code that is in a separate file to prevent clutter

`multiprocess.py`: testing for python multiprocessing; currently unfinished

## Other
I am currently working on better ways to restrict the sample space and multiprocessing. With the current setup it takes
about 100 minutes to solve each level past level 100. This program should be stable enough to leave running overnight.
Running for about 15 hours got me to level 116 which puts me comfortably in the top 5-20% of solvers.