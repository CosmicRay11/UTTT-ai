## 2-player UTTT

import numpy as np
import random
import tkinter as tk
# don't bother with ttk, it's unnecessary

##DTI: board is valid
class Board(object):

    def __init__(self, filename=None):

        self.empty = "E"
        self.X = "X"
        self.O = "O"

        self.estr = "E"
        self.xstr = "X"
        self.ostr = "O"

        self.stateDict = {"X win":"X", "O win":"O", "draw":"D", "full":"F", "ongoing":"E"}

        # convert between string representation and the underlying array representation of an O, X or empty
        self.strDict = {self.xstr:self.X, self.ostr:self.O, self.estr:self.empty}

        # an array of Move type objects that are the moves made by both players. For undoing and redoing moves
        self.moves = []

        # the underlying array storing the state of the game. Indexed with 4 numbers, each 0 to 2. x,y,i and j describe the local (x,y) grid and the (i,j) position within it
        self.grid = np.array([[[[self.empty for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)])

        # the next player to make a move
        self.next_player = self.xstr
        
        ## The next grid to be played in. None to start with, but a 2-tuple describing a local grid otherwise. (None if the player can play anywhere)
        self.next_grid = None 

        # if a file is supplied, load the board state
        if filename != None:
            with open(filename, 'r') as file:
                filestring = file.read().replace("\n", "")
                self.load_board(filestring)

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
        for y in range(3):
            for j in range(3):
                for x in range(3):
                    for i in range(3):
                        s = filestring[counter]                            
                        self.grid[x][y][i][j] = self.strDict[s]
                        counter += 1

    ## save the board to a given filename (must be a .txt file)
                        ## format is as described above
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

    ## return the current state of the board, i.e. win, loss, draw (including inevitable draws) or ongoing
    # states are from the dictionary self.stateDict
    def game_state(self):
        # set up a mini 3x3 grid, showing the state of each of the local grids 
        minigrid = []
        for x in range(3):
            minigrid.append([])
            for y in range(3):
                localState = self.local_game_state(x,y)
                if self.inevitable_draw(self.convert_minigrid_to_state(self.grid[x][y])):
                    localState = self.stateDict["draw"]
                minigrid[x].append(localState)
        
        state = self.stateDict["ongoing"]

        # assign the grid a "won" state if one player has won
        for i in range(3):
             # vertical case
            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == self.stateDict["ongoing"] and minigrid[i][0] in [self.stateDict["X win"], self.stateDict["O win"]]:
                state = minigrid[i][0]
            # horizontal case
            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == self.stateDict["ongoing"] and minigrid[0][i] in [self.stateDict["X win"], self.stateDict["O win"]]:
                state = minigrid[0][i]
         # diagonal case
        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == self.stateDict["ongoing"] and minigrid[1][1] in [self.stateDict["draw"], self.stateDict["full"]]:
            state = minigrid[1][1]   

        # assign the grid either a draw or ongoing state if neither player has won
        # the grid is drawn if the current player has no further moves, or if a draw is inevitable
        if state == self.stateDict["ongoing"]:
            moves = len(self.get_valid_moves())
            if moves == 0 or self.inevitable_draw(minigrid):
                state = self.stateDict["draw"]
        
        return state

    ## returns a boolean indicating if a draw is inevitable based on a 3x3 minigrid of state
    def inevitable_draw(self, minigrid):
        winnable = False
        ## check if vertical, horizontal or diagonal winning lines exist. If none exist, then a draw is inevitable
        for i in range(3):
            if self.winnable_line(minigrid[i][0], minigrid[i][1], minigrid[i][2]):
                winnable = True
            if self.winnable_line(minigrid[0][i], minigrid[1][i], minigrid[2][i]):
                winnable = True
        if self.winnable_line(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.winnable_line(minigrid[2][0], minigrid[1][1], minigrid[0][2]):
            winnable = True
        return not winnable

    ## return whether, given the state of 3 squares, a winning line may be made from them
    def winnable_line(self, a, b, c):
        full = self.stateDict["draw"]
        if a == full or b == full or c == full:
            return False

        xwin = self.stateDict["X win"]
        owin = self.stateDict["O win"]
        xPresent = a == xwin or b== xwin or c == xwin
        oPresent = a == owin or b== owin or c == owin
        return not(xPresent and oPresent)   # based upon the truth table - should be false only if Xpresent and O present are both True

    ## convert a 3x3 minigrid of underlying representations to a 3x3 minigrid of "state" characters (i.e. "X")
    def convert_minigrid_to_state(self, minigrid):
        for i in range(3):
            for j in range(3):
                if minigrid[i][j] == self.X:
                    minigrid[i][j] = self.stateDict["X win"]
                elif minigrid[i][j] == self.O:
                    minigrid[i][j] = self.stateDict["O win"]
                elif minigrid[i][j] == self.empty:
                    minigrid[i][j] = self.stateDict["ongoing"]
        return minigrid
    

    ## return the state of a 3x3 grid within the main grid, at position x,y (0 <= x, y <= 2)
    # E for empty and in play, F for full, drawn and done, X for X win and done, O for O win and done
    def local_game_state(self, x,y):
        minigrid = self.convert_minigrid_to_state(self.grid[x][y])
        state = self.stateDict["ongoing"]
        for i in range(3):
            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == self.stateDict["ongoing"]: # verticals
                state = minigrid[i][0]
            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == self.stateDict["ongoing"]: # horizontals
                state = minigrid[0][i]
        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == self.stateDict["ongoing"]: # diagonals
            state = minigrid[1][1]

        if state == self.stateDict["ongoing"]:
            count = 0
            for i in range(3):
                for j in range(3):
                    if np.array_equal(minigrid[i][j], self.empty):
                        count += 1
            if count == 0:
                state = self.stateDict["full"]
        return state


    def square_done(self, x, y):
        return self.local_game_state(x,y) != self.stateDict["ongoing"]

    # useful if the state is changed to an array, allows changing the implementation  ###############################
    def convert_state_to_str(self, state):
        if state == self.X:
            return self.xstr
        if state == self.O:
            return self.ostr
        if state == self.empty:
            return self.estr

    def change_player(self):
        if self.next_player == self.xstr:
            self.next_player = self.ostr
        else:
            self.next_player = self.xstr

    def update_next_grid(self, x, y):
        if self.square_done(x,y):
            self.next_grid = None
        else:
            self.next_grid = (x,y)

    def make_move(self,x,y,i,j):
        
        if (self.next_grid == None or (x,y) == self.next_grid) and self.grid[x][y][i][j] == self.empty and not self.square_done(x,y):
            self.grid[x][y][i][j] = self.strDict[self.next_player]
            newMove = Move((x,y,i,j), self.next_player, self.next_grid)
            self.moves.append(newMove)
            
            self.update_next_grid(i,j)
            self.change_player()

    def un_make_move(self):
        if len(self.moves) != 0:
            move = self.moves.pop(-1)
            x,y,i,j = move.pos
            self.grid[x][y][i][j] = self.empty
            self.next_player = move.player
            self.next_grid = move.localgrid

    def equal3(self, a, b, c):
        return a == b and b == c

    def get_valid_moves(self):
        moves = []
        if self.next_grid == None:
            for x in range(3):
                for y in range(3):
                    if not self.square_done(x,y):
                        for i in range(3):
                            for j in range(3):
                                if self.grid[x][y][i][j] == self.empty:
                                    moves.append((x,y,i,j))
        else:
            x,y = self.next_grid
            if not self.square_done(x,y):
                for i in range(3):
                    for j in range(3):
                        if self.grid[x][y][i][j] == self.empty:
                            moves.append((x,y,i,j))
        return moves


class Move():

    def __init__(self, pos, player, localgrid):
        self.pos = pos
        self.player = player
        self.localgrid = localgrid

class Tree():

    def __init__(self, board):
        self.board = board
        self.parent = Node()

        self.moves = []
    

    def is_leaf(self, node=None):
        return True

class Node():

    def __init__(self, parent=None):
        self.num = 0
        self.den = 0

#board[x][y] describes a local board
#board[x][y][i][j] describes a position on the local board x,y


class GUI():
    
    def __init__(self, master, board):
        self.master = master
        master.title("Ultimate Tic Tac Toe")
        self.board = board

        self.title = tk.Label(master, text="Ultimate Tic Tac Toe", font = ("Courier, 12"))
        self.title.pack()

        self.next_player_var = tk.StringVar()
        self.next_player_var.set(board.next_player + " to play")
        
        self.next_player_label = tk.Label(master, textvariable = self.next_player_var, font = ("Courier, 12"))
        self.next_player_label.pack(pady = 10)


        self.grid = BoardGUI(master, board, self.update_widgets)
        self.grid.pack()

    def update_widgets(self):
        state = self.board.game_state()
        string = ""
        if state == self.board.stateDict["ongoing"]:
            string = self.board.next_player + " to play"
        elif state == self.board.stateDict["draw"]:
            string = "Game Drawn"
        elif state == self.board.stateDict["X win"]:
            string = "Game Won by X"
        elif state == self.board.stateDict["O win"]:
            string = "Game Won by O"

        self.next_player_var.set(string)


    def update(self):
        self.grid.update()


class BoardGUI(tk.Frame):
    def __init__(self, parent, board, update_foo, *args, **kwargs):
        tk.Frame.__init__(self, parent)

        self.buttons = {}
        self.board = board
        self.update_foo = update_foo

        self.xcol = "red"
        self.ocol = "blue"
        self.backcol = "grey"
        self.ecol = "light grey"
        
        self.create()
        
        self.squareify(self.mainFrame)

        self.update()

    def squareify(self, frame, string="fred"):
        frame.grid_columnconfigure(0, weight=1, uniform=string)
        frame.grid_columnconfigure(1, weight=1, uniform=string)
        frame.grid_columnconfigure(2, weight=1, uniform=string)
        frame.grid_rowconfigure(0, weight=1, uniform=string)
        frame.grid_rowconfigure(1, weight=1, uniform=string)
        frame.grid_rowconfigure(2, weight=1, uniform=string)
        return frame

    def create(self):
        self.mainFrame = tk.Frame(bg = self.backcol)
        self.mainFrame.pack(fill = "both", expand = True)
        self.subframes = {}
        for x in range(3):
            for y in range(3):
                state = self.board.local_game_state(x,y)
                
                newFrame = tk.Frame(self.mainFrame, padx=10, pady=10, borderwidth = 5, relief="groove", bg = self.backcol)
                newFrame = self.squareify(newFrame, "fred")
                    
                for i in range(3):
                    for j in range(3):
                        key = str(x) + str(y) + str(i) + str(j)
                        play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                        button = tk.Button(newFrame, text = "   ", padx = 5, pady = 5, borderwidth=2, relief="groove")
                        button.grid(row=i, column=j, ipadx = 10, ipady = 10)
                        self.buttons[key] = button

                newFrame.grid(row=x, column=y)
                self.subframes[str(x)+str(y)] = newFrame

        self.update()
        self.update_foo()
        

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
                                if (x,y,i,j) in self.board.get_valid_moves():  # need to abstract this type of method
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

        self.update_foo()

        if self.board.game_state() != self.board.stateDict["ongoing"]:
            for x in range(3):
                for y in range(3):
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            button = self.buttons[key]
                            button.config(command = self.none_cmd, relief = "flat")
                            

    def none_cmd(self):
        pass

    def button_cmd(self, x,y,i,j):
        self.board.make_move(x,y,i,j)
        self.update()

        

board = Board()

root = tk.Tk()
gui = GUI(root, board)
root.mainloop()

