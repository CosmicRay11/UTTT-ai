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

    def consider_moves(self, board):
        pass
