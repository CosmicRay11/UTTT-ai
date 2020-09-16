## Ultimate Tic Tac Toe project

import tkinter as tk
from MCTS import MCTS
from GameManager import GameManager

import pandas as pd

import cProfile

import sys, os
OUTPUT = sys.stdout

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = OUTPUT


openingsPath = "openings.csv"
cols = ["board", "end state"]

try:
    data = pd.read_csv(openingsPath)
except FileNotFoundError:
    print("yay")
    data = pd.DataFrame(columns = cols)

    data.to_csv(openingsPath)



for i in range(500):
    b = Board()
    p1 = MCTS()
    p2 = MCTS()

    newData = pd.DataFrame(columns = cols)

    p1Player = b.xstr
    while b.game_state() != b.stateDict["ongoing"]:
        start = time.time()
        endTime = start + self.aiTime

        lastMove = b.get_last_move()

        if b.next_player == p1Player:
            p1.move(b, endTime, b.next_player, lastMove)
        else:
            p2.move(b, endTime, b.next_player, lastMove)

        p1ToPlay = not p1ToPlay
    
    data

input()
blockPrint()



enablePrint()

print(manager.board.grid)

root = tk.Tk()
man = GameManager(None, None, root = root, file = "recent.txt")

##for i in range(10):
##    manager.start_game(True)
##    manager.reset()


# cython board is really worth it, 2x speed improvement
