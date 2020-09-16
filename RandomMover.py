from Strat import Strat
import random

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
