import tkinter as tk

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

    def reset_board(self, board):
        self.board = board
        self.grid.board = board


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

    # an empty command (used to easily disable buttons without showing their "disabled" state visually)
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
