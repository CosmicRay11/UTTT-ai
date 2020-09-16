import time
from Board import Board
from GUI_Classes import GUI


## a class to manage the interaction between player and AI, while keeping the GUI alive
class GameManager():

    def __init__(self, p1Strat, p2Strat, root=None, file=None, time_limit=5):

        self.board = Board(file)

        self.p1Strat, self.p2Strat = p1Strat, p2Strat

        self.file = file

        self.ai1 = None
        self.ai2 = None
        
        if p1Strat != None:
            self.ai1 = p1Strat(self.board, self.update_root)
        if p2Strat != None:
            self.ai2 = p2Strat(self.board, self.update_root)

        self.root = root

        self.displayingGUI = self.root != None

        if self.displayingGUI:
            self.gui = GUI(root, self.board)

        
        
        self.aiTime = time_limit

        self.update_root()

    ## update the root gui manually
    def update_root(self):
        if self.displayingGUI:
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

        if self.displayingGUI:
            self.gui.update()
            self.update_root()

        
        boardCopy = self.board.copy()
        lastMove = None
        
        print("start game")
        ## if the ai player is playing, make their move, otherwise wait and update the gui
        while self.board.game_state() == self.board.stateDict["ongoing"]:
            move = self.board.get_last_move()
            if move != lastMove:
                x,y,i,j = move
                boardCopy.make_move(x,y,i,j)
                lastMove = move
                print(self.board.export())
                if self.displayingGUI:
                    self.gui.update(False) ## is this false?
            if self.board.next_player == firstString and self.ai1 != None:
                self.start_ai_move(self.ai1)
                if self.displayingGUI:
                    self.gui.update(True)
            elif self.board.next_player != firstString and self.ai2 != None:
                self.start_ai_move(self.ai2)
                if self.displayingGUI:
                    self.gui.update(True)
            else:
                
                if self.board.next_player == firstString and self.ai2 != None:
                    self.ai2.consider_moves(boardCopy)
                elif self.board.next_player != firstString and self.ai1 != None:
                    self.ai1.consider_moves(boardCopy)

            self.update_root()

        if self.displayingGUI:
            self.gui.update()

        self.board.save_board("recent.txt")
        
            
    ## start the ai processing to make a move
    def start_ai_move(self, ai):
        if self.displayingGUI:
            self.gui.show_ai_deciding()
        start = time.time()
        endTime = start + self.aiTime

        lastMove = self.board.get_last_move()
        
        ai.move(self.board, endTime, self.board.next_player, lastMove)

    def reset(self):
        
        self.board = Board()
        if self.displayingGUI:
            self.gui.reset_board(self.board)
        
        if self.p1Strat != None:
            self.ai1 = self.p1Strat(self.board, self.update_root)
        if self.p2Strat != None:
            self.ai2 = self.p2Strat(self.board, self.update_root)
        
        self.gui.show_pre_game()
        self.gui.update()

        self.update_root()
