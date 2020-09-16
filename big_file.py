## monte-carlo tree search for UTTT with visual display
## version 1, pure MCTS

## comment terminology : local board/grid refers to a 3x3 normal tic tac toe board, global refers to the 3x3x3x3 ultimate board

import numpy as np
import random
import tkinter as tk
import time
import copy
import math
import cProfile
import re


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
        """TODO needs to be altered to undo cached cacheGrid moves I think - at least needs testing before introduce an undo move button """
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
        if len(self.moves) != 0:
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

## create a tkinter GUI for playing against an AI opponent
class GUI():
    
    def __init__(self, master, board, playerStarts = False):
        self.master = master
        self.board = board

        self.master.title("Ultimate Tic Tac Toe")

        self.title = tk.Label(master, text="Ultimate Tic Tac Toe", font = ("Courier, 12"))
        self.title.pack()

        self.next_player_var = tk.StringVar()
        self.next_player_var.set("Game not in play")
        
        self.next_player_label = tk.Label(master, textvariable = self.next_player_var, font = ("Courier, 12"))
        self.next_player_label.pack(pady = 10)

        self.grid = BoardGUI(master, board)
        self.grid.pack()

        self.show_pre_game()
        
    ## alter widgets when the ai is deciding on a move
    def show_ai_deciding(self):
        self.grid.disable_buttons()
        self.next_player_var.set("{} deciding where to play".format(self.board.next_player))

    ## alter widgets when the game is not started yet
    def show_pre_game(self):
        self.grid.disable_buttons()
        self.next_player_var.set("Game not yet in play")
   
    ## an centralised update function that updates the gui and its contents to reflect the board state
    def update(self, aiPlayer=False):
        self.grid.update()
        state = self.board.game_state()
        string = ""
        if state == self.board.stateDict["ongoing"]:
            if not aiPlayer:
                string = self.board.next_player + " to play"
        elif state == self.board.stateDict["draw"]:
            string = "Game Drawn"
        elif state == self.board.stateDict["X win"]:
            string = "Game Won by X"
        elif state == self.board.stateDict["O win"]:
            string = "Game Won by O"

        if not aiPlayer:
            self.next_player_var.set(string)


## a specialised frame to display the contents of a UTTT board
class BoardGUI(tk.Frame):
    def __init__(self, parent, board, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.buttons = {}
        self.board = board

        self.xcol = "red"
        self.ocol = "blue"
        self.backcol = "grey"
        self.ecol = "light grey"

        self.altXcol = "pink"
        self.altOcol = "light blue"
        self.highlightcol = "green"

        ## create the widgets in this frame
        self.create()
        
        self.squareify(self.mainFrame)

        self.update()

    ## make the contents of a frame align in a square fashion
    def squareify(self, frame, string="nonuniquestr"):
        frame.grid_columnconfigure(0, weight=1, uniform=string)
        frame.grid_columnconfigure(1, weight=1, uniform=string)
        frame.grid_columnconfigure(2, weight=1, uniform=string)
        frame.grid_rowconfigure(0, weight=1, uniform=string)
        frame.grid_rowconfigure(1, weight=1, uniform=string)
        frame.grid_rowconfigure(2, weight=1, uniform=string)
        return frame

    ## create all the subframes and widgets in this class
    ## each local board has its own frame, stored in the dictionary self.subframes, within which are 9 buttons in a 3x3 pattern, stored in the dictionary seld.buttons
    def create(self):
        self.mainFrame = tk.Frame(bg = self.backcol)
        self.mainFrame.pack(fill = "both", expand = True)
        self.subframes = {}
        for x in range(3):
            for y in range(3):
                newFrame = tk.Frame(self.mainFrame, padx=10, pady=10, borderwidth = 5, relief="groove", bg = self.backcol)
                newFrame = self.squareify(newFrame, str(x) + str(y))
                for i in range(3):
                    for j in range(3):
                        key = str(x) + str(y) + str(i) + str(j)
                        play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                        button = tk.Button(newFrame, text = "   ", padx = 5, pady = 5, borderwidth=2, relief="groove")
                        button.grid(row=i, column=j, ipadx = 10, ipady = 10)
                        self.buttons[key] = button

                newFrame.grid(row=x, column=y)
                self.subframes[str(x)+str(y)] = newFrame

        ## update the buttons to give them their contents
        self.update()        


    ## update the contents and colour of the buttons and their frames to reflect the board state
    def update(self):
        
        if self.board.next_player == self.board.xstr:
            cursorString = "cross"
        else:
            cursorString = "circle"
        self.mainFrame.config(cursor = cursorString)
        
        for x in range(3):
            for y in range(3):
                state = self.board.local_game_state(x,y)
                frame = self.subframes[str(x)+str(y)]
                
                if state == self.board.stateDict["ongoing"]:
                    if (self.board.next_grid == (x,y) or self.board.next_grid == None) and self.board.game_state() == self.board.stateDict["ongoing"]:
                        frame.config(bg = self.highlightcol)
                    else:
                        frame.config(bg = self.backcol)
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                            button = self.buttons[key]
                            if play == self.board.xstr:
                                button.config(background = self.xcol, text = "X", padx = 5, pady = 5, relief = "groove")
                            elif play == self.board.ostr:
                                button.config(background = self.ocol, text = "O", padx = 5, pady = 5, relief = "groove")
                            else:
                                if (x,y,i,j) in self.board.get_valid_moves():
                                    cmd = lambda x=x, y=y, i=i, j=j : self.button_cmd(x,y,i,j)
                                    button.config(background = self.ecol,  text = "   ", padx = 5, pady = 5, command = cmd, borderwidth=2, relief="raised")
                                else:
                                    button.config(text = "   ", padx = 5, pady = 5, borderwidth=2, relief="flat", command = self.none_cmd)
                else:
                    if state == self.board.stateDict["full"]:
                        col = self.ecol
                    elif state == self.board.stateDict["X win"]:
                        col = self.xcol
                    elif state == self.board.stateDict["O win"]:
                        col = self.ocol
                    frame.config(bg=col)
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            button = self.buttons[key]
                            button.config(bg = col, relief = "groove")
                            play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                            if play == self.board.xstr:
                                button.config(text = "X")
                            elif play == self.board.ostr:
                                button.config(text = "O")

        ## disable the buttons if the game is over
        if self.board.game_state() != self.board.stateDict["ongoing"]:
            for x in range(3):
                for y in range(3):
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            button = self.buttons[key]
                            button.config(command = self.none_cmd, relief = "flat")

        ## show the last move to be made in a different colour
        else:
            lastMove = self.board.get_last_move()
            if lastMove != None:
                x,y,i,j = lastMove
                key = str(x) + str(y) + str(i) + str(j)
                button = self.buttons[key]
                play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                if play == self.board.xstr:
                    button.config(bg = self.altXcol)
                elif play == self.board.ostr:
                    button.config(bg = self.altOcol)

    # an empty command (used to easily disable buttons without showing their "disabled" state
    def none_cmd(self):
        pass

    ## disable all buttons
    def disable_buttons(self):
        for button in self.buttons.values():
            button.config(command = self.none_cmd)

    ## the command the buttons invoke upon being pressed - i.e. attempt to make a move and update the gui
    def button_cmd(self, x,y,i,j):
        self.board.make_move(x,y,i,j)
        self.update()

## a class to manage the interaction between player and AI, while keeping the GUI alive
class GameManager():

    def __init__(self, root, p1Strat, p2Strat, file=None, time_limit=5):

        self.board = Board(file)

        self.p1Strat, self.p2Strat = p1Strat, p2Strat

        self.file = file

        self.ai1 = None
        self.ai2 = None
        
        if p1Strat != None:
            self.ai1 = p1Strat(self.board, self.update_root)
        if p2Strat != None:
            self.ai2 = p2Strat(self.board, self.update_root)
        
        self.gui = GUI(root, self.board)

        self.root = root
        
        self.aiTime = time_limit

    ## update the root gui manually
    def update_root(self):
        self.root.update()

    ## start the game loop
    def start_game(self, X_first):
        if X_first:
            firstString = self.board.xstr
        else:
            firstString = self.board.ostr

        if self.file != None: ## weak, doesn't ensure successful load from file...
            firstString = self.board.next_player
        else:
            self.board.next_player = firstString
        
        self.gui.update()

        ## if the ai player is playing, make their move, otherwise wait and update the gui
        while self.board.game_state() == self.board.stateDict["ongoing"]:
            
            if self.board.next_player == firstString and self.ai1 != None:
                self.start_ai_move(self.ai1)
                self.gui.update(True)
            elif self.board.next_player != firstString and self.ai2 != None:
                self.start_ai_move(self.ai2)
                self.gui.update(True)
            else:
                self.gui.update(False)

            self.update_root()

        self.gui.update()

        self.board.save_board("recent.txt")
        
            
    ## start the ai processing to make a move
    def start_ai_move(self, ai):
        self.gui.show_ai_deciding()
        start = time.time()
        endTime = start + self.aiTime

        lastMove = self.board.get_last_move()
        
        ai.move(self.board, endTime, self.board.next_player, lastMove)

    def reset(self):
        self.board = Board()
        
        if self.p1Strat != None:
            self.ai1 = self.p1Strat(self.board, self.update_root)
        if self.p2Strat != None:
            self.ai2 = self.p2Strat(self.board, self.update_root)

# parent class for any ai strategy
class Strat():

    def __init__(self, board, update_foo=None):
        if update_foo == None:
            self.update_root = self.empty_foo
        else:
            self.update_root = update_foo

    def empty_foo(self):
        pass

    # choose and implement a move on the board
    def move(self, board, endTime, aiString="X", oppMove = None):
        pass

## make a random valid move as a strategy
class RandomMover(Strat):
     def __init__(self, board = None, update_foo=None):
        Strat.__init__(self, board, update_foo)
        
     def move(self, board, endTime=None, aiString = "X", oppMove = None):
        
        moves = board.get_valid_moves()
        assert(len(moves) > 0)
        while time.time() < endTime:
            self.update_root()
        move = random.choice(moves)
        x,y,i,j = move
        board.make_move(x,y,i,j)


## pure monte-carlo tree search, using a random playout as the simulation step
## Leaf node: any node with a child from which no simulation has taken place
class MCTS(Strat):

    def __init__(self, board, update_foo=None):
        board = board.copy()
        Strat.__init__(self, board, update_foo)
        self.tree = Tree(board)

    ## function to update the search tree to have a new root
    def update_tree(self, newRoot, board):
        #board = copy.deepcopy(board)
        board = board.copy()
        self.tree = Tree(board)
        self.tree.root = newRoot
        self.tree.root.parent = None
        self.tree.root.move = None

    ## make and implement a move using the MCTS strategy
    def move(self, board, endTime, aiString="X", oppMove=None):
        
        # if the opponent has made a move, traverse the tree so that the root node is in the right place
        # if the tree is not positioned correctly to facilitate such a traversal, just reset the tree to a blank search tree
        if oppMove != None:
            children = self.tree.root.children
            oppNode = None
            for child in children:
                if child.move == oppMove:
                    oppNode = child
            if oppNode != None:
                self.update_tree(oppNode, board)
            else:
                self.tree = Tree(board)
        else:
            self.tree = Tree(board)

        boardCopy = board.copy()
        
        ## for the allotted search time, build up information about the search tree
        count = 0
        while time.time() < endTime:

            ## select a leaf node (currently using a heuristic formula to choose nodes that explore promising deep variants and a lot of shallow variants also)
            boardCopy, leaf, moveCounter = self.selection(boardCopy, self.tree.root, aiString)

            ## choose a child of the leaf (at random)
            child = self.expansion(boardCopy, leaf)

            ## carry out a simulation of the game from the child node and use this info to update the game tree
            self.simulation(boardCopy, child, aiString)

            for a in range(moveCounter):
                boardCopy.un_make_move()

            # update the gui, if applicable
            self.update_root()
            count += 1

        ## get the node corresponding to the best move (move with highest ratio of successful playouts)
        bestMoveNode = self.choose_best_move(aiString)
        x,y,i,j = bestMoveNode.move

        # make the move on the board
        board.make_move(x,y,i,j)

        # update the root of the tree to the best move node
        #self.update_tree(bestMoveNode, copy.deepcopy(board))
        self.update_tree(bestMoveNode, board.copy())

        print("Count is: {}".format(count), "Total moves is: {}".format(board.totalMoves))
        
        
    ## select a leaf node to explore the game tree from
    def selection(self, board, root, aiString):
        node = root
        counter = 0
        while not node.is_leaf():
            lastNode = node
            maximumScore = 0
            bestNodes = []
            for child in node.children:
                score = self.select_express(child, node, aiString)
                if score > maximumScore:
                    bestNodes = [child]
                
            node = max((child for child in node.children), key = lambda x: self.select_express(x, node, aiString))
            x,y,i,j = node.move
            board.make_move(x,y,i,j)
            counter += 1
        return board, node, counter

    def select_express(self, child, parent, aiString):
        wi = child.num
        ni = float(child.den)
        Ni = parent.den
        c = 1.4142
        if ni == 0:
            return float("inf")
        else:
            return wi/ni + c * ((math.log(Ni)/ ni) ** 0.5)

    ## expand the game tree from a leaf node, and select a child node to conduct a simulation from
    def expansion(self, board, parent):
        state = board.game_state()
        if state == board.stateDict["ongoing"]:
            if not parent.hasChildren:
                moves = board.get_valid_moves()
                for move in moves:
                    self.tree.add_node(move, parent)
                parent.hasChildren = True
            children = parent.children
            childChoice = random.choice(children)
            ## currently a random choice, not a random choice of nodes that haven't been simulated
            return childChoice
        else:
            return parent
        
    # simulate one playout from a node, and backpropagate the information this gives along the game tree
    def simulation(self, board, node, aiString): # param unnecc TODO
        node.do_simulate_update()
        counter = 0
        while board.game_state() == board.stateDict["ongoing"]:
            moves = board.get_valid_moves()
            if counter < 0:
                move = max((move for move in moves), key = lambda x: self.simulate_heuristic(x, board)) 
            else:
                move = random.choice(moves)
            counter += 1
            x,y,i,j = move
            board.make_move(x,y,i,j)
        state = board.game_state()
        #print("simulation result is " + state)
        if state == board.stateDict["X win"]:
            if node.player == board.xstr:
                score = 1
            else:
                score = 0
        elif state == board.stateDict["O win"]:
            if node.player == board.ostr:
                score = 1
            else:
                score = 0
        else:
            score = 0.5

        #print(self.tree)
        self.back_propagate(node, score, board)
        #print(self.tree)

        for a in range(counter):
            board.un_make_move()

    # 
    def simulate_heuristic(self, move, board):
        #return random.random()
        moves = board.get_valid_moves()

        x,y,i,j = move
        player = board.next_player

        board.make_move(x,y,i,j)

        gameState = board.game_state()
        
        if (gameState == board.stateDict["X win"] and player == board.xstr) or (gameState == board.stateDict["O win"] and player == board.ostr):
            score = float("inf") # maximum score because you win!
        elif (gameState == board.stateDict["X win"] and player == board.ostr) or (gameState == board.stateDict["O win"] and player == board.xstr):
            score = -float("inf") # minimum score because you lose!
        else:
            score = random.random()
        
        score = 0
        for a in range(3):
            for b in range(3):
                lines = board.get_local_lines(a,b, player)
                lineSum = sum(sum(t for t in line) for line in lines)
                score += lineSum

        globalLines = board.get_global_lines(player)
        score += 10 * sum(sum(t for t in line) for line in globalLines) # heuristic
        board.un_make_move()
            
        return score

    ## back propagate the result of a simulation along the game tree
    def back_propagate(self, node, score, board):
        while node.parent != None:
            node.den += 1
            node.num += score
            score = 1 - score
            node = node.parent
        
        node.den += 1
        node.num += score

    ## select the best move for the current player to make, given the current state of the game tree - the node with greatest denominator
    def choose_best_move(self, aiString):
        children = self.tree.root.children
        maximum = 0
        bestMoves = []
        for c in children:
            print(c)
            if c.den == maximum:
                maximum = c.den
                bestMoves.append(c)
            elif c.den > maximum:
                bestMoves = [c]
                maximum = c.den

        return random.choice(bestMoves)

## a custom tree class for use in the MCTS strat
class Tree():

    def __init__(self, board):
        self.board = board
        self.root = Node(None, None, board.player_just_played())

    def add_node(self, move, parent):
        if parent.player == self.board.xstr:
            player = self.board.ostr
        else:
            player = self.board.xstr
        node = Node(parent, move, player)
        parent.add_child(node)
        return node

    def is_root(self, node):
        return node.parent == None

    def __repr__(self):
        return self.printout([self.root])

    def printout(self, nodes, maxdepth = 3, indent = 0):
        string = ""
        if indent < maxdepth:
            for node in nodes:
                string += "  " * indent + str(node) + "\n"
                if node.hasChildren:
                    string += self.printout(node.children, maxdepth, indent + 1)
        return string

## a node in the game tree
class Node():
    def __init__(self, parent, move, player):
        self.num = 0
        self.den = 0
        self.parent = parent
        self.children = []
        self.move = move
        self.player = player

        ## variables for checking whether a node is a leaf or not, and for knowing when to create new child nodes from it
        self.childMoveCount = 0
        self.hasSimulated = False
        self.hasChildren = False
        
    def __repr__(self):
        if self.parent != None:
            return "Parent: {} || Ratio {} / {} || Move: {} || Player: {}".format(self.parent.move, self.num, self.den, self.move, self.player)
        else:
            return "Parent: ISROOT || Ratio {} / {} || Move: {} || Player: {}".format(self.num, self.den, self.move, self.player)

    def add_child(self, node):
        self.children.append(node)

    ## leaf nodes have a potential child node that hasn't been simulated from yet
    def is_leaf(self):
        if not self.hasChildren:
            return True
        if len(self.children) == self.childMoveCount:
            return True
        return False

    ## update a node when a simulation from it has occurred
    def do_simulate_update(self):
        self.update_parent_leafy()
        self.hasSimulated = True

    ## update the node's parent info on whether the parent is a leaf or not
    def update_parent_leafy(self):
        if self.parent != None:
            self.parent.childMoveCount += 1


root = tk.Tk()
root.resizable(height = False, width = False)

manager = GameManager(root, MCTS, None, time_limit=5)
manager.start_game(True)
