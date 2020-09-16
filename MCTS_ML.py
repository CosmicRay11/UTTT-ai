import random
import time
import math
from Strat import Strat
import numpy as np

from MCTS import MCTS, Tree, Node
from Board import Board


## pure monte-carlo tree search, using a random playout as the simulation step
## Leaf node: any node with a child from which no simulation has taken place
class MCTS_ML(MCTS):

    def __init__(self, board, neuralNet, update_foo=None):
        MCTS.__init__(self, board, update_foo)
        self.neuralNet = neuralNet

    def policy_empty(self, policy):
        return type(policy) == type(None)

    ## select a leaf node to explore the game tree from
    def selection(self, board, root):
        node = root
        counter = 0
        while not node.is_leaf():
            lastNode = node
            maximumScore = 0
            bestNodes = []
            if self.policy_empty(node.policy):
                node.policy = Board.unflatten(self.neuralNet.predict(board.export().reshape(1,9,9))[0])
            policy = node.policy
            
            for child in node.children:
                x,y,i,j = child.move
                prob = policy[x,y,i,j]   # causing errors with policy not being the correct shape
                score = self.select_express(child, node, prob)
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

    def select_express(self, child, parent, prob):
        wi = child.num
        ni = float(child.den)
        Ni = parent.den
        c = 1.4142
        if ni == 0:
            return float("inf")
        else:                           
            return wi/ni + c * prob * ((Ni)**0.5) / (1+ni)

        
    # simulate one playout from a node, and backpropagate the information this gives along the game tree
    def simulation(self, board, node):
        node.do_simulate_update()
    
        prediction = self.neuralNet.predict(board.export().reshape(1,9,9))

        score = prediction[1][0][0]
        policy = prediction[0]
        if self.policy_empty(node.policy):
            node.policy = policy
        #print(self.tree)
        self.back_propagate(node, score, board)
        #print(self.tree)


    ## back propagate the result of a simulation along the game tree
    def back_propagate(self, node, score, board):
        while node.parent != None:
            node.den += 1
            node.num += score
            score = 1 - score                                       #      """ may need to be altered in this implementation, if the end scores are not compressed to 1 to 0   """
            node = node.parent
        
        node.den += 1
        node.num += score
