## Ultimate Tic Tac Toe project

import tkinter as tk
from MCTS import MCTS
from GameManager import GameManager

import cProfile

import sys, os
OUTPUT = sys.stdout

## alphazero uses 800 searches per move

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = OUTPUT

#blockPrint()
#enablePrint()

#root = tk.Tk()
#root.resizable(height = False, width = False)
#enablePrint()

manager = GameManager(MCTS, MCTS, root = None, time_limit=0.5)
manager.start_game(True)

enablePrint()

print(manager.board.grid)

root = tk.Tk()
man = GameManager(None, None, root = root, file = "recent.txt")

##for i in range(10):
##    manager.start_game(True)
##    manager.reset()


# cython board is really worth it, 2x speed improvement
