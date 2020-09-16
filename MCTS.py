import random
import time
import math
from Strat import Strat



## pure monte-carlo tree search, using a random playout as the simulation step
## Leaf node: any node with a child from which no simulation has taken place
class MCTS(Strat):

    def __init__(self, board, update_foo=None):
        board = board.copy()
        Strat.__init__(self, board, update_foo)
        self.tree = Tree(board)

    ## function to update the search tree to have a new root node
    def update_tree(self, newRoot, board):
        #board = copy.deepcopy(board)
        board = board.copy()
        self.tree = Tree(board)
        self.tree.root = newRoot
        self.tree.root.parent = None
        self.tree.root.move = None

    ## update the search tree to have a new root node, given the last move
    def update_tree_nodeless(self, board, oppMove):
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

    ## make and implement a move using the MCTS strategy
    def move(self, board, endTime, aiString="X", oppMove=None):
        
        # if the opponent has made a move, traverse the tree so that the root node is in the right place
        # if the tree is not positioned correctly to facilitate such a traversal, just reset the tree to a blank search tree

        self.update_tree_nodeless(board, oppMove)

        boardCopy = board.copy()
        
        ## for the allotted search time, build up information about the search tree
        count = 0
        while time.time() < endTime:

            self.consider_moves(boardCopy)

            # update the gui, if applicable
            self.update_root()
            count += 1

        ## get the node corresponding to the best move (move with highest ratio of successful playouts)
        bestMoveNode = self.choose_best_move()
        x,y,i,j = bestMoveNode.move

        # make the move on the board
        board.make_move(x,y,i,j)

        # update the root of the tree to the best move node
        #self.update_tree(bestMoveNode, copy.deepcopy(board))
        self.update_tree(bestMoveNode, board.copy())

        print("Count is: {}".format(count), "Total moves is: {}".format(board.totalMoves))
        
        
        
    ## select a leaf node to explore the game tree from
    def selection(self, board, root):
        node = root
        counter = 0
        while not node.is_leaf():
            lastNode = node
            maximumScore = 0
            bestNodes = []
            for child in node.children:
                score = self.select_express(child, node)
                if score > maximumScore:
                    bestNodes = [child]
                    maximumScore = score
                elif score == maximumScore:
                    bestNodes.append(child)
                
            node = random.choice(bestNodes)
            x,y,i,j = node.move
            board.make_move(x,y,i,j)
            counter += 1
        return board, node, counter

    def select_express(self, child, parent):
        wi = child.num
        ni = float(child.den)
        Ni = parent.den
        c = 1.4142
        if ni == 0:
            return float("inf")
        else:
            return wi/ni + c * ((math.log(Ni)/ ni) ** 0.5)  ## or different expression in neural net version

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
    def simulation(self, board, node):
        node.do_simulate_update()
        counter = 0
        while board.game_state() == board.stateDict["ongoing"]:
            moves = board.get_valid_moves()
##            if board.totalMoves > 35:
##                move = max((move for move in moves), key = lambda x: self.simulate_heuristic(x, board))
##            else:
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
        
##        score = 0
##        for a in range(3):
##            for b in range(3):
##                lines = board.get_local_lines(a,b, player)
##                lineSum = sum(sum(t for t in line) for line in lines)
##                score += lineSum
##
##        globalLines = board.get_global_lines(player)
##        score += 10 * sum(sum(t for t in line) for line in globalLines) # heuristic

            
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
    def choose_best_move(self):
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

    def consider_moves(self, boardCopy):

        #print(self.tree.root)
        ## select a leaf node (currently using a heuristic formula to choose nodes that explore promising deep variants and a lot of shallow variants also)
        boardCopy, leaf, moveCounter = self.selection(boardCopy, self.tree.root)

        ## choose a child of the leaf (at random)
        child = self.expansion(boardCopy, leaf)

        ## carry out a simulation of the game from the child node and use this info to update the game tree
        self.simulation(boardCopy, child)

        for a in range(moveCounter):
            boardCopy.un_make_move()

        #print("considering")

        return boardCopy
        

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
        self.posScore = None
        self.policy = None

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
