## monte-carlo tree search for UTTT
## version 1, pure MCTS

import numpy as np
import random
import tkinter as tk
# don't bother with ttk, it's unnecessary

##DTI: board is valid
class Board(object):

    def __init__(self, filename=None):
        self.empty = np.array([1,0,0])
        self.X = np.array([0,1,0])
        self.O = np.array([0,0,1])

        self.estr = "E"
        self.xstr = "X"
        self.ostr = "O"

        self.strDict = {self.xstr:self.X, self.ostr:self.O, self.estr:self.empty}

        self.moves = []

        self.grid = np.array([[[[self.empty for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)])
        self.next_player = self.xstr
        self.next_grid = None ## none to start with, but a 2-tuple of the grid otherwise. None if the player can play anywhere
        
        if filename != None:
            self.grid = np.array([[[[self.empty for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)])
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

    ## return the current state of the board, i.e. win, loss, draw or in-play  ----> not doing drawing/in-play yet
    def game_state(self):
        minigrid = []
        for x in range(3):
            minigrid.append([])
            for y in range(3):
                minigrid[x].append(self.local_game_state(self.grid[x][y]))
        state = "E"

        # win grid
        for i in range(3):
            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == "E": # verticals
                state = minigrid[i][0]
            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == "E": # horizontals
                state = minigrid[0][i]
        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == "E": # diagonals
            state = minigrid[1][1]
        
        if state == "E":
            winnable = False
            for i in range(3):
                if self.winnable_line(minigrid[i][0], minigrid[i][1], minigrid[i][2]):
                    winnable = True
                if self.winnable_line(minigrid[0][i], minigrid[1][i], minigrid[2][i]):
                    winnable = True
            if self.winnable_line(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.winnable_line(minigrid[2][0], minigrid[1][1], minigrid[0][2]):
                winnable = True
            if not winnable:
                state = "D" # for drawn

            moves = len(self.get_valid_moves())
            if moves == 0:
                state = "D"
        
        return state

    def winnable_line(self, a, b, c):
        if a == "F" or b == "F" or c == "F":
            return False
        xPresent = a == "X" or b=="X" or c == "X"
        oPresent = a == "O" or b=="O" or c == "O"
        return not(xPresent and oPresent)   # based upon the truth table - should be false only if Xpresent and O present are both True

    ## return the state of a 3x3 grid within the main grid, at position x,y (0 <= x, y <= 2), as either empty or X or O
    # E for empty and in play, F for full and done, X for X win and done, O for O win and done
    def local_game_state(self, minigrid):
        state = "E"
        for i in range(3):
            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == "E": # verticals
                state = self.convert_state_to_str(minigrid[i][0])
            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == "E": # horizontals
                state = self.convert_state_to_str(minigrid[0][i])
        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == "E": # diagonals
            state = self.convert_state_to_str(minigrid[1][1])

        if state == "E":
            count = 0
            for i in range(3):
                for j in range(3):
                    if np.array_equal(minigrid[i][j], self.empty):
                        count += 1
            if count == 0:
                state = "F"
        return state


    def square_done(self, minigrid):
        return self.local_game_state(minigrid) != "E"

    def convert_state_to_str(self, state):
        if np.array_equal(state, self.X):
            return self.xstr
        if np.array_equal(state, self.O):
            return self.ostr
        if np.array_equal(state, self.empty):
            return self.estr

    def change_player(self):
        if self.next_player == self.xstr:
            self.next_player = self.ostr
        else:
            self.next_player = self.xstr

    def update_next_grid(self, x, y):
        if self.square_done(self.grid[x][y]):
            self.next_grid = None
        else:
            self.next_grid = (x,y)

    def make_move(self,x,y,i,j):
        
        if (self.next_grid == None or (x,y) == self.next_grid) and np.array_equal(self.grid[x][y][i][j], self.empty) and not self.square_done(self.grid[x][y]):
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
        return np.array_equal(a,b) and np.array_equal(b,c)

    def get_valid_moves(self):
        moves = []
        if self.next_grid == None:
            for x in range(3):
                for y in range(3):
                    if not self.square_done(self.grid[x][y]):
                        for i in range(3):
                            for j in range(3):
                                if np.array_equal(self.grid[x][y][i][j], self.empty):
                                    moves.append((x,y,i,j))
        else:
            x,y = self.next_grid
            if not self.square_done(self.grid[x][y]):
                for i in range(3):
                    for j in range(3):
                        if np.array_equal(self.grid[x][y][i][j], self.empty):
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
        if state == "E":
            string = self.board.next_player + " to play"
        elif state == "D":
            string = "Game Drawn"
        elif state == "X":
            string = "Game Won by X"
        elif state == "O":
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
                state = self.board.local_game_state(self.board.grid[x][y])
                
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
        
        if self.board.next_player == "X":
            cursorString = "cross"
        else:
            cursorString = "circle"
        self.mainFrame.config(cursor = cursorString)
        for x in range(3):
            for y in range(3):
                state = self.board.local_game_state(self.board.grid[x][y])
                frame = self.subframes[str(x)+str(y)]
                if state == "E":
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                            button = self.buttons[key]
                            if play == "X":
                                button.config(background = self.xcol, text = "X", padx = 5, pady = 5)
                            elif play == "O":
                                button.config(background = self.ocol, text = "O", padx = 5, pady = 5)
                            else:
                                if (x,y,i,j) in self.board.get_valid_moves():  # need to abstract this type of method
                                    cmd = lambda x=x, y=y, i=i, j=j : self.button_cmd(x,y,i,j)
                                    button.config(background = self.ecol,  text = "   ", padx = 5, pady = 5, command = cmd, borderwidth=2, relief="raised")
                                else:
                                    button.config(text = "   ", padx = 5, pady = 5, borderwidth=2, relief="flat", command = self.none_cmd)
                else:
                    if state == "F":
                        col = self.ecol
                    elif state == "X":
                        col = self.xcol
                    elif state == "O":
                        col = self.ocol
                    frame.config(bg=col)
                    for i in range(3):
                        for j in range(3):
                            key = str(x) + str(y) + str(i) + str(j)
                            button = self.buttons[key]
                            button.config(bg = col, relief = "groove")
                            play = self.board.convert_state_to_str(self.board.grid[x][y][i][j])
                            if play == "X":
                                button.config(text = "X")
                            elif play == "O":
                                button.config(text = "O")

        self.update_foo()


        if self.board.game_state() != "E":
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

