## monte-carlo tree search for UTTT with visual display
## version 1, pure MCTS

import numpy as np
import random
import tkinter as tk
import time
import copy
# don't bother with ttk, it's unnecessary

##DTI: board is valid
class Board(object):

    def __init__(self, filename=None):
        #self.empty = np.array([1,0,0])
        #self.X = np.array([0,1,0])
        #self.O = np.array([0,0,1])

        self.estr = "E"
        self.xstr = "X"
        self.ostr = "O"

        self.stateDict = {"X win":self.xstr, "O win":self.ostr, "draw":"D", "full":"F", "ongoing":self.estr}

        self.moves = []

        self.grid = np.array([[[[self.estr for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)])
        self.next_player = self.xstr
        self.next_grid = None ## none to start with, but a 2-tuple of the grid otherwise. None if the player can play anywhere
        
        if filename != None:
            self.grid = np.array([[[[self.estr for i in range(3)] for j in range(3)] for k in range(3)] for l in range(3)])
            with open(filename, 'r') as file:
                filestring = file.read().replace("\n", "")
                self.load_board(filestring)


        ## need to make this compatible with starting a game partway through TODO!!!#################################################################################
        self.localLinesX = [[ [[0,0,0],[0,0,0],[0,0]] for y in range(3)] for x in range(3)]   # caching the number of Xs in each line of each local board, given by verticals, horizontals and diagonals
        self.localLinesO = [[ [[0,0,0],[0,0,0],[0,0]] for y in range(3)] for x in range(3)]  # same for Os
        self.cacheGrid = [[self.local_game_state(x,y) for y in range(3)] for x in range(3)]
        self.globalLinesX = [[0,0,0],[0,0,0],[0,0]]
        self.globalLinesO = [[0,0,0],[0,0,0],[0,0]]

        self.totalMoves = 0


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
                        self.grid[x][y][i][j] = s
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

        ##minigrid = []
        ##minigrid = self.cacheGrid
        
##        # has the grid been won? If, so assign it this state
##        for i in range(3):
##            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == self.stateDict["ongoing"] and minigrid[i][0] in [self.stateDict["X win"], self.stateDict["O win"]]: # verticals
##                state = minigrid[i][0]
##            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == self.stateDict["ongoing"] and minigrid[0][i] in [self.stateDict["X win"], self.stateDict["O win"]]: # horizontals
##                state = minigrid[0][i]
##        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == self.stateDict["ongoing"] and minigrid[1][1] in [self.stateDict["draw"], self.stateDict["full"]]: # diagonals
##            state = minigrid[1][1]
        
        if state == self.stateDict["ongoing"]:
            #draw = self.inevitable_draw(minigrid)
            draw = self.inevitable_draw_cached(self.globalLinesX, self.globalLinesO)
            if draw:
                state = self.stateDict["draw"]
            else:
                if self.totalMoves == 81:
                    state = self.stateDict["draw"]
        
        return state

    def update_cacheGrid(self, x,y, moveForward = True):
        current = self.cacheGrid[x][y]
        self.cacheGrid[x][y] = self.local_game_state(x,y)
        #if self.inevitable_draw(self.convert_minigrid_to_state(self.grid[x][y])):
        if self.inevitable_draw_cached(self.localLinesX[x][y], self.localLinesO[x][y]):
            self.cacheGrid[x][y] = self.stateDict["draw"]
        if self.cacheGrid[x][y] != current:
            self.update_globalLines(x,y, moveForward)

    def update_lines(self, lines, h, v, add):
        lines[0][h] += add # add 1 to the horizontal line counter in line i
        lines[1][v] += add # add 1 to the vertical line counter in line j
        if h == v:
            lines[2][0] += add # diagonal #1
        if h + v == 2:
            lines[2][1] += add # diagonal #2
        return lines

    def update_globalLines(self, x,y, moveForward = True):
        if moveForward:
            add = 1
        else:
            add = -1
        if self.next_player == self.xstr:
            self.globalLinesX = self.update_lines(self.globalLinesX, x, y, add)
        else:
            self.globalLinesO = self.update_lines(self.globalLinesO, x, y, add)

    def update_localLines(self, x,y,i,j, moveForward=True):
        if moveForward:
            add = 1
        else:
            add = -1
        if self.next_player == self.xstr:
            self.localLinesX[x][y] = self.update_lines(self.localLinesX[x][y], i, j, add)
        else:
            self.localLinesO[x][y] = self.update_lines(self.localLinesO[x][y], i, j, add)

    def inevitable_draw(self, minigrid):
        winnable = False
        for i in range(3):
            if self.winnable_line(minigrid[i][0], minigrid[i][1], minigrid[i][2]):
                winnable = True
            if self.winnable_line(minigrid[0][i], minigrid[1][i], minigrid[2][i]):
                winnable = True
        if self.winnable_line(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.winnable_line(minigrid[2][0], minigrid[1][1], minigrid[0][2]):
            winnable = True
        return not winnable

    def inevitable_draw_cached(self, linesX, linesO):
        for a in range(len(linesX)):
            for b in range(len(linesX[a])):
                lineX, lineO = linesX[a][b], linesO[a][b]
                if not (lineX > 0 and lineO > 0):
                    return False
        return True

    def winnable_line(self, a, b, c):
        full = self.stateDict["draw"]
        if a == full or b == full or c == full:
            return False

        xwin = self.stateDict["X win"]
        owin = self.stateDict["O win"]
        xPresent = a == xwin or b== xwin or c == xwin
        oPresent = a == owin or b== owin or c == owin
        return not(xPresent and oPresent)   # based upon the truth table - should be false only if Xpresent and O present are both True

    def convert_minigrid_to_state(self, minigrid):
        for i in range(3):
            for j in range(3):
                if minigrid[i][j] == self.xstr:
                    minigrid[i][j] = self.stateDict["X win"]
                elif minigrid[i][j] == self.ostr:
                    minigrid[i][j] = self.stateDict["O win"]
                elif minigrid[i][j] == self.estr:
                    minigrid[i][j] = self.stateDict["ongoing"]
        return minigrid

    ## return the state of a 3x3 grid within the main grid, at position x,y (0 <= x, y <= 2), as either empty or X or O
    # E for empty and in play, F for full and done, X for X win and done, O for O win and done
    def local_game_state(self, x,y):
        state = self.stateDict["ongoing"]
        for direction in self.localLinesX[x][y]:
            for line in direction:
                if line == 3:
                    state = self.stateDict["X win"]
        
        for direction in self.localLinesO[x][y]:
            for line in direction:
                if line == 3:
                    state = self.stateDict["O win"]

        if state == self.stateDict["ongoing"]:
            count = 0
            for i in range(3):
                for j in range(3):
                    if self.grid[x][y][i][j] == self.estr:
                        count += 1
            if count == 0:
                state = self.stateDict["full"]
        
        return state
        
##        minigrid = self.convert_minigrid_to_state(self.grid[x][y])
##        state = self.stateDict["ongoing"]
##        for i in range(3):
##            if self.equal3(minigrid[i][0], minigrid[i][1], minigrid[i][2]) and state == self.stateDict["ongoing"]: # verticals
##                state = minigrid[i][0]
##            elif self.equal3(minigrid[0][i], minigrid[1][i], minigrid[2][i]) and state == self.stateDict["ongoing"]: # horizontals
##                state = minigrid[0][i]
##        if self.equal3(minigrid[0][0], minigrid[1][1], minigrid[2][2]) or self.equal3(minigrid[2][0], minigrid[1][1], minigrid[0][2]) and state == self.stateDict["ongoing"]: # diagonals
##            state = minigrid[1][1]
##
##        if state == self.stateDict["ongoing"]:
##            count = 0
##            for i in range(3):
##                for j in range(3):
##                    if minigrid[i][j] == self.estr:
##                        count += 1
##            if count == 0:
##                state = self.stateDict["full"]
        return state


    def square_done(self, x, y):
        return self.local_game_state(x,y) != self.stateDict["ongoing"]

    # useful if the state is changed to an array, allows changing the implementation  ###############################
    def convert_state_to_str(self, state):
        return state

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
        
        if (self.next_grid == None or (x,y) == self.next_grid) and self.grid[x][y][i][j] == self.estr and not self.square_done(x,y):
            self.grid[x][y][i][j] = self.next_player
            newMove = MoveMemento((x,y,i,j), self.next_player, self.next_grid)
            self.moves.append(newMove)

            self.update_localLines(x,y,i,j, True)  
            self.update_cacheGrid(x,y, True)
            
            self.update_next_grid(i,j)
            self.change_player()

            self.totalMoves += 1

            

    def un_make_move(self):
        if len(self.moves) != 0:
            move = self.moves.pop(-1)
            x,y,i,j = move.pos
            
            self.grid[x][y][i][j] = self.estr
            self.next_player = move.player
            self.next_grid = move.localgrid

            self.update_localLines(x,y,i,j, False)
            self.update_cacheGrid(x,y, False)

            self.totalMoves -= 1

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
                                if self.grid[x][y][i][j] == self.estr:
                                    moves.append((x,y,i,j))
        else:
            x,y = self.next_grid
            if not self.square_done(x,y):
                for i in range(3):
                    for j in range(3):
                        if self.grid[x][y][i][j] == self.estr:
                            moves.append((x,y,i,j))
        return moves

    def get_last_move(self):
        if len(self.moves) > 0:
            move = self.moves[-1]
            return move.pos
        else:
            return None


class MoveMemento():

    def __init__(self, pos, player, localgrid):
        self.pos = pos
        self.player = player
        self.localgrid = localgrid

#board[x][y] describes a local board
#board[x][y][i][j] describes a position on the local board x,y


class GUI():
    
    def __init__(self, master, board, strat, playerStarts = False):
        self.master = master
        master.title("Ultimate Tic Tac Toe")
        self.board = board

        self.title = tk.Label(master, text="Ultimate Tic Tac Toe", font = ("Courier, 12"))
        self.title.pack()

        self.next_player_var = tk.StringVar()
        self.next_player_var.set("Game not in play")
        
        self.next_player_label = tk.Label(master, textvariable = self.next_player_var, font = ("Courier, 12"))
        self.next_player_label.pack(pady = 10)

        self.grid = BoardGUI(master, board, self.update_widgets)
        self.grid.pack()

        self.strat = strat

        self.show_pre_game()
        

    def show_ai_deciding(self):
        self.grid.disable_buttons()
        self.next_player_var.set("{} deciding where to play".format(self.board.next_player))

    def show_pre_game(self):
        self.grid.disable_buttons()
        self.next_player_var.set("Game not yet in play")

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

        self.altXcol = "pink"
        self.altOcol = "light blue"
        self.highlightcol = "green"
        
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

    def none_cmd(self):
        pass

    def disable_buttons(self):
        for button in self.buttons.values():
            button.config(command = self.none_cmd)

    def button_cmd(self, x,y,i,j):
        self.board.make_move(x,y,i,j)
        self.update()

class GameManager():

    def __init__(self, board, gui, strat1, strat2):

        self.board = board
        self.gui = gui
        self.strat1 = strat1
        self.strat2 = strat2
        
        self.aiTime = 5
        self.aiString = None # first ai string 

    def start_game(self, X_first, ai_first):
        if X_first:
            self.board.next_player = self.board.xstr
        else:
            self.board.next_player = self.board.ostr

        if ai_first:
            if X_first:
                self.aiString = self.board.xstr
            else:
                self.aiString = self.board.ostr
        else:
            if X_first:
                self.aiString = self.board.ostr
            else:
                self.aiString = self.board.xstr
            self.gui.update()

        while self.board.game_state() == self.board.stateDict["ongoing"]:
            global root
            if self.board.next_player == self.aiString:
                self.gui.show_ai_deciding()
                start = time.time()
                endTime = start + self.aiTime
                move = self.strat1.move(self.board, endTime, self.board.next_player)  
                x,y,i,j = move
                self.board.make_move(x,y,i,j)
                self.gui.update()
            else:
                self.gui.show_ai_deciding()
                start = time.time()
                endTime = start + self.aiTime
                move = self.strat2.move(self.board, endTime, self.board.next_player)  
                x,y,i,j = move
                self.board.make_move(x,y,i,j)
                self.gui.update()

            self.gui.update()
            root.update()

    def start_ai_move(self):
        self.gui.show_ai_deciding()
        start = time.time()
        endTime = start + self.aiTime

        move = self.strat.move(self.board, endTime, self.aiString)  
        x,y,i,j = move
        self.board.make_move(x,y,i,j)

        self.gui.update()
        

# parent class for any ai strategy
class Strat():

    def __init__(self, board):
        pass

    def move(self, board, endTime):
        pass

    def update_root(self):
        global root
        root.update()
        pass

class RandomMover(Strat):
     def __init__(self, board = None):
        Strat.__init__(self, board)
        
     def move(self, board, endTime=None, *args):
        
        moves = board.get_valid_moves()
        assert(len(moves) > 0)
        #while time.time() < endTime:
            #self.update_root()
        move = random.choice(moves)
        return move


class MCTS(Strat):

    def __init__(self, board):
        board = copy.deepcopy(board)
        Strat.__init__(self, board)
        self.tree = Tree(board)

    def move(self, board, endTime, aiString="X"):
        
        #print(self.tree.nodes)
        board = copy.deepcopy(board)
        self.tree = Tree(board)
        boardCopy = copy.deepcopy(board)

        count = 0
        while time.time() < endTime:
            
            boardCopy = copy.deepcopy(board)

            boardCopy, leaf = self.selection(boardCopy, self.tree.root)
            child = self.expansion(boardCopy, leaf)
            self.simulation(boardCopy, child)

            self.update_root()
            count += 1

        #print(count)

        bestMove = self.choose_best_move(aiString)
        

        print(bestMove)
        print(count)
        #for n in self.tree.nodes:
            #print(n.num, n.den)

        return bestMove
        
        

    def selection(self, board, root):
        node = root
        while not node.is_leaf():
            node = random.choice(node.children)
            x,y,i,j = node.move
            board.make_move(x,y,i,j)
        return board, node
            
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
            return childChoice
        else:
            return parent
        

    def simulation(self, board, node):
        node.update_parent_leafy()
        while board.game_state() == board.stateDict["ongoing"]:
            moves = board.get_valid_moves()
            
            x,y,i,j = random.choice(moves)
            board.make_move(x,y,i,j)

        

        state = board.game_state()
        if state == board.stateDict["X win"]:
            score = 1
        elif state == board.stateDict["O win"]:
            score = 0
        else:
            score = 0.5

        #for m in range(moveCounter):
            #board.un_make_move()

        self.back_propagate(node, score)

    def back_propagate(self, node, score):
        #print(node.index)
        while node.parent != None:
            node.den += 1
            node.num += score # check this
            node = node.parent
        
        node.num += score
        node.den += 1


    def choose_best_move(self, aiString):
        children = self.tree.root.children
        #print(children, aiString)
        if aiString == board.ostr:
            minimum = 1
            bestMove = None
            for c in children:
                print(c)
                if c.den != 0:
                    ratio = float(c.num) / c.den
                else:
                    ratio = 0.5
                print(ratio)
                if ratio <= minimum:
                    minimum = ratio
                    bestMove = c.move
        else:
            maximum = 0
            bestMove = None
            for c in children:
                print(c)
                if c.den != 0:
                    ratio = float(c.num) / c.den
                else:
                    ratio = 0.5
                print(ratio)
                if ratio >= maximum:
                    maximum = ratio
                    bestMove = c.move

        return bestMove

class Tree():

    def __init__(self, board):
        self.board = board
        self.root = Node(None, None)
        self.nodeCount = 0

    def add_node(self, move, parent):
        node = Node(parent, move)
        parent.add_child(node)
        self.nodeCount += 1
        return node

    def is_root(self, node):
        return node.parent == None


class Node():
    def __init__(self, parent, move):
        self.num = 0
        self.den = 0
        self.parent = parent
        self.children = []
        self.move = move
        self.childMoveCount = 0
        
        self.hasChildren = False
        
    def __repr__(self):
        if self.parent != None:
            return "Parent: {} || Ratio {} / {} || Move: {}".format(self.parent.move, self.num, self.den, self.move)
        else:
            return "Parent: ISROOT || Ratio {} / {} || Move: {}".format(self.num, self.den, self.move)

    def add_child(self, node):
        self.children.append(node)

    def is_leaf(self):
        if not self.hasChildren:
            return True
        if len(self.children) == self.childMoveCount:
            return True
        return False

    def update_parent_leafy(self):
        if self.parent != None:
            self.parent.childMoveCount += 1

board = Board()
ai1 = MCTS(board)
ai2 = RandomMover(board)

##x,y,i,j = ai.move(board, time.time()+1, "X")
##board.make_move(x,y,i,j)
##x,y,i,j = ai.move(board, time.time()+1, "O")
##board.make_move(x,y,i,j)
##x,y,i,j = ai.move(board, time.time()+1, "X")
##board.make_move(x,y,i,j)
##x,y,i,j = ai.move(board, time.time()+1, "O")
##board.make_move(x,y,i,j)


root = tk.Tk()
gui = GUI(root, board, ai1, ai2)

manager = GameManager(board, gui, ai1, ai2)

manager.start_game(True, False)

#root.mainloop()

