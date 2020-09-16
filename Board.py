## Ultimate Tic Tac Toe Board implementation

## comment terminology : local board/grid refers to a 3x3 normal tic tac toe board, global refers to the 3x3x3x3 ultimate board

import random
import tkinter as tk
import time
import copy
import math
import numpy as np

##DTI: board is valid && line caches remain valid && moves retains the sequence of moves leading to the board state && 
class Board(object):

    def __init__(self, filename=None):

        self.estr = "E"
        self.xstr = "X"
        self.ostr = "O"

        # store strings for various board states
        self.stateDict = {"X win":self.xstr, "O win":self.ostr, "draw":"D", "full":"F", "ongoing":self.estr}

        # a list of MoveMementos in order of the moves that have been made - for undoing moves
        self.moves = []

        # the (3x3)x(3x3) grid storing whether each mini square is a X, O or empty
        self.grid = [[[[self.estr for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)]
        self.next_player = self.xstr
        self.next_grid = None # the local grid that the next player is to play into. None if the player can play anywhere, a 2-tuple of local grid coordinates otherwise

        self.totalMoves = 0
        
        # potentially load up a stored game from a text file
        if filename != None:
            with open(filename, 'r') as file:
                filestring = file.read().replace("\n", "")
                self.load_board(filestring)
    
        # set up caches (storing grid data O(1) performance on key functions)
        self.load_caches()

    ## represent the board state with the current player as 1s, the opposition as -1, and empty spaces as 0.1
    def export(self):
        array = np.zeros((3,3,3,3))
        for x in range(3):
            for y in range(3):
                state = self.local_game_state(x,y)
                if (state == self.stateDict["X win"] and self.next_player == self.xstr) or (state == self.stateDict["O win"] and self.next_player == self.ostr):
                    array[x,y] += 1
                elif (state == self.stateDict["X win"] and self.next_player == self.ostr) or (state == self.stateDict["O win"] and self.next_player == self.xstr):
                    array[x,y] -= 1
                else:
                    for a in range(9):
                        i,j = divmod(a, 3)
                        if self.grid[x][y][i][j] == self.next_player:
                            array[x,y,i,j] = 1
                        elif self.grid[x][y][i][j] == self.estr:
                            array[x,y,i,j] = 0.1
                        else:
                            array[x,y,i,j] = -1
        
        return Board.flatten_2D(array)

    def flatten_2D(array):
        return np.reshape(array, (9,9))

    def flatten(array):
        return np.reshape(array, (81,))

    def unflatten(array):
        return np.reshape(array, (3,3,3,3))

    def letter_to_int(self, letter):
        if letter == self.next_player:
            return 1
        if letter == self.player_just_played():
            return -1
        else:
            return 0.1

    # loads the board from a string
    # string[0] = next player's character
    # string[1] = next player's grid x       or      N if can play anywhere
    # string[2] = next player's grid y  -  
    # string[3:81] is the board position, read left to right and top to bottom
    def load_board(self, filestring):
        
        self.next_player = filestring[0]
        if filestring[1] == "N":
            self.next_grid = None
        else:
            self.next_grid = (int(filestring[1]), int(filestring[2]))
        filestring = filestring[3:]
        counter = 0
        for x in range(3):
            for i in range(3):
                for y in range(3):
                    for j in range(3):
                        s = filestring[counter]                            
                        self.grid[x][y][i][j] = s
                        if s != self.estr:
                            self.totalMoves += 1
                        counter += 1

    ## saves the current board state to a given filename
    def save_board(self, filename):
        filestring = self.next_player
        if self.next_grid == None:
            filestring += "NA"
        else:
            filestring += str(self.next_grid[0]) + str(self.next_grid[1])
        for y in range(3):
            for j in range(3):
                filestring += "\n"
                for x in range(3):
                    for i in range(3):
                        filestring += self.convert_state_to_str(self.grid[x][y][i][j])
        with open(filename, "w") as file:
            file.write(filestring)

    ## initialise key caches that improve performance.
    # In particular, each 3x3 grid (local and global) has the number of Xs and Os in each line stored so that the state of the grid can be ascertained efficiently
    def load_caches(self):
        self.localLinesX = [[ [[0,0,0],[0,0,0],[0,0]] for y in range(3)] for x in range(3)]   # caching the number of Xs in each line of each local board, given by verticals, horizontals and diagonals
        self.localLinesO = [[ [[0,0,0],[0,0,0],[0,0]] for y in range(3)] for x in range(3)]  # same for Os

        self.emptySquaresDict = {}

        for x in range(3):
            for y in range(3):
                self.emptySquaresDict[str(x)+str(y)] = []
                for i in range(3):
                    for j in range(3):
                        if self.grid[x][y][i][j] == self.xstr:
                            self.update_lines(self.localLinesX[x][y], i, j, 1)
                        elif self.grid[x][y][i][j] == self.ostr:
                            self.update_lines(self.localLinesO[x][y], i, j, 1)
                        else:
                            self.emptySquaresDict[str(x)+str(y)].append((x,y,i,j))

        ## do the same process as for the local board for the global board
        self.globalLinesX = [[0,0,0],[0,0,0],[0,0]]
        self.globalLinesO = [[0,0,0],[0,0,0],[0,0]]

        for x in range(3):
            for y in range(3):
                state = self.calculate_local_game_state(x,y)
                if state == self.stateDict["X win"]:
                    self.update_lines(self.globalLinesX, x, y, 1)
                elif state == self.stateDict["O win"]:
                    self.update_lines(self.globalLinesO, x, y, 1)

        # cache the current global board state (just the 3x3 global view)
        self.cacheGrid = [[self.calculate_local_game_state(x,y) for y in range(3)] for x in range(3)]

        for x in range(3):
            for y in range(3):
                if self.square_done(x,y):
                    self.emptySquaresDict[str(x)+str(y)] = []

    ## update all the caches after a move (x,y,i,j) has been made
    ## moveForward denotes whether the move is being made or undone (True = new move made)
    def update_caches(self, x, y, i, j, moveForward = True):
        
        self.update_localLines(x,y,i,j, moveForward)

        current = self.cacheGrid[x][y]
        self.cacheGrid[x][y] = self.calculate_local_game_state(x,y)
        if self.inevitable_draw_cached(self.localLinesX[x][y], self.localLinesO[x][y]):
            #self.cacheGrid[x][y] = self.stateDict["draw"]
            pass

        if moveForward:
            if self.cacheGrid[x][y] != current and self.cacheGrid[x][y] in [self.stateDict["X win"], self.stateDict["O win"]] and current in [self.stateDict["full"], self.stateDict["ongoing"]]:
                self.update_globalLines(x,y, moveForward)
        else:
            if self.cacheGrid[x][y] != current and current in [self.stateDict["X win"], self.stateDict["O win"]] and self.cacheGrid[x][y] in [self.stateDict["full"], self.stateDict["ongoing"]]:
                self.update_globalLines(x,y, moveForward)

        key = str(x)+str(y)
        if moveForward:
            if self.square_done(x,y):
                self.emptySquaresDict[key] = []
            else:
                 self.emptySquaresDict[key].remove((x,y,i,j))
        else:
            if not self.square_done(x,y):
                self.emptySquaresDict[key] = []
                for a in range(3):
                    for b in range(3):
                        if self.grid[x][y][a][b] == self.estr:
                            self.emptySquaresDict[key].append((x,y,a,b))
            else:
                self.emptySquaresDict[key] = []

    ## helper function to update the number of symbols in a 3x3 grid on each key line
    ## lines is the storage list (e.g. self.globalLines, or self.localLines[0][0]) 
    def update_lines(self, lines, h, v, add):
        lines[0][h] += add # add 1 to the horizontal line counter in line i
        lines[1][v] += add # add 1 to the vertical line counter in line j
        if h == v:
            lines[2][0] += add # diagonal #1
        if h + v == 2:
            lines[2][1] += add # diagonal #2
        return lines

    ## update the local line caches after a move
    def update_localLines(self, x,y,i,j, moveForward=True):
        if moveForward:
            add = 1
        else:
            add = -1
        if self.next_player == self.xstr:
            self.localLinesX[x][y] = self.update_lines(self.localLinesX[x][y], i, j, add)
        else:
            self.localLinesO[x][y] = self.update_lines(self.localLinesO[x][y], i, j, add)

    ## update the global line caches after a move
    def update_globalLines(self, x,y, moveForward = True):
        if moveForward:
            add = 1
        else:
            add = -1
        if self.next_player == self.xstr:
            self.globalLinesX = self.update_lines(self.globalLinesX, x, y, add)
        else:
            self.globalLinesO = self.update_lines(self.globalLinesO, x, y, add)

    ## return the current state of the board, i.e. win, loss, draw (including inevitable draws) or in-play
    def game_state(self):
        
        state = self.stateDict["ongoing"]

        for direction in self.globalLinesX:
            for line in direction:
                if line == 3:
                    state = self.stateDict["X win"]
        
        for direction in self.globalLinesO:
            for line in direction:
                if line == 3:
                    state = self.stateDict["O win"]

        if state == self.stateDict["ongoing"]:
           
            if self.inevitable_draw_cached(self.globalLinesX, self.globalLinesO) or len(self.get_valid_moves()) == 0:
                state = self.stateDict["draw"]
        
        return state

    ## get a line list of a local board for a given player
    def get_local_lines(self, x, y, player):
        if player == self.xstr:
            return self.localLinesX[x][y]
        elif player == self.ostr:
            return self.localLinesO[x][y]

    ## get the correct line list of the global board for a given player
    def get_global_lines(self, player):
        if player == self.xstr:
            return self.globalLinesX
        elif player == self.ostr:
            return self.globalLinesO

    ## helper function to determine whether a 3x3 grid is in an inevitable draw situation, given the line caches for the grid
    def inevitable_draw_cached(self, linesX, linesO):
        for a in range(len(linesX)):
            for b in range(len(linesX[a])):
                lineX, lineO = linesX[a][b], linesO[a][b]
                if not (lineX > 0 and lineO > 0):
                    return False
        return True

    ## returns if a given line (a,b,c) can be won by either play. a, b and c are states in self.stateDict
    def winnable_line(self, a, b, c):
        full = self.stateDict["draw"]
        if a == full or b == full or c == full:
            return False

        xwin = self.stateDict["X win"]
        owin = self.stateDict["O win"]
        xPresent = a == xwin or b== xwin or c == xwin
        oPresent = a == owin or b== owin or c == owin
        return not(xPresent and oPresent)   # based upon the truth table - should be false only if Xpresent and Opresent are both True

    ## calculate and return the state of a local 3x3 grid within the global grid, at position x,y (0 <= x, y <= 2)
    def calculate_local_game_state(self, x, y):
        for direction in self.localLinesX[x][y]:
            for line in direction:
                if line == 3:
                    return self.stateDict["X win"]
        
        for direction in self.localLinesO[x][y]:
            for line in direction:
                if line == 3:
                    return self.stateDict["O win"]

        # neither won so must still be ongoing or drawn
        count = 0
        for i in range(3):
            for j in range(3):
                if self.grid[x][y][i][j] == self.estr:
                    return self.stateDict["ongoing"]
        #all squares must be full so return full
        return self.stateDict["full"]

    ## return the state of a local 3x3 grid within the global grid, at position x,y (0 <= x, y <= 2)
    # states are : E for empty and in play, F for full and done, X for X win and done, O for O win and done (the symbols in self.stateDict)
    def local_game_state(self, x,y):
        return self.cacheGrid[x][y]

    ## return if a local 3x3 grid can't be played in
    def square_done(self, x, y):
        return self.local_game_state(x,y) != self.stateDict["ongoing"]

    # a function to convert the state of a self.grid square to a string
    ## present to abstract out the board representation (it just happens that the board represents xs and os as strings currently)
    def convert_state_to_str(self, state):
        return state

    ## change the self.next_player variable to the other player
    def change_player(self):
        if self.next_player == self.xstr:
            self.next_player = self.ostr
        else:
            self.next_player = self.xstr

    ## update the self.next_grid variable to show where the next player has to play
    def update_next_grid(self, x, y):
        if self.square_done(x,y):
            self.next_grid = None
        else:
            self.next_grid = (x,y)

    ## make a move (x,y,i,j) on the board, provided it is valid
    ## store the move as a memento in the self.moves list
    def make_move(self,x,y,i,j):
        if (self.next_grid == None or (x,y) == self.next_grid) and self.grid[x][y][i][j] == self.estr and not self.square_done(x,y):
            self.grid[x][y][i][j] = self.next_player
            newMove = MoveMemento((x,y,i,j), self.next_player, self.next_grid)

            self.update_caches(x,y,i,j,True)
            
            self.update_next_grid(i,j)
            self.change_player()
            
            self.moves.append(newMove)
            self.totalMoves += 1
        else:
            print("move failed ({} {} {} {})".format(x,y,i,j))
            pass
            
    ## undo the last move made
    def un_make_move(self):
        if len(self.moves) > 0:
            self.totalMoves -= 1
            
            move = self.moves.pop(-1)
            x,y,i,j = move.pos

            self.next_player = move.player
            self.next_grid = move.localgrid
            self.grid[x][y][i][j] = self.estr

            self.update_caches(x,y,i,j,False)

            

    ## test if three variables are equal (assuming transitivity)
    def equal3(self, a, b, c):
        return a == b and b == c

    ## get a list of valid moves for the next player
    def get_valid_moves(self):
        moves = []
        if self.next_grid == None:
            for x in range(3):
                for y in range(3):
                    moves += self.emptySquaresDict[str(x)+str(y)]
                        
        else:
            x,y = self.next_grid
            moves = self.emptySquaresDict[str(x)+str(y)]
                
        #return moves
        moves1 = list(moves)
        return list(moves)

    ## get the last move played
    def get_last_move(self):
        if len(self.moves) > 0:
            move = self.moves[-1]
            return move.pos
        else:
            return None

    ## create a copy of this board
    def copy(self):
        return copy.deepcopy(self)
        newBoard = Board()

        newBoard.grid = copy.deepcopy(self.grid)
        newBoard.moves = list(self.moves) # mementos are not mutable so this does not need to be a deep copy
        newBoard.next_player = str(self.next_player)
        newBoard.next_grid = self.next_grid
        newBoard.totalMoves = int(self.totalMoves)
        
        newBoard.localLinesX = copy.deepcopy(self.localLinesX)
        newBoard.localLinesO = copy.deepcopy(self.localLinesO)
        newBoard.globalLinesX = copy.deepcopy(self.globalLinesX)
        newBoard.globalLinesO = copy.deepcopy(self.globalLinesO)
        newBoard.cacheGrid = copy.deepcopy(self.cacheGrid)
        newBoard.emptySquaresDict = copy.deepcopy(self.emptySquaresDict)

        return newBoard

    def player_just_played(self):
        if self.next_player == self.xstr:
            return self.ostr
        return self.xstr


## store data that allows a move to be undone
class MoveMemento():

    def __init__(self, pos, player, localgrid):
        self.pos = pos
        self.player = player
        self.localgrid = localgrid

