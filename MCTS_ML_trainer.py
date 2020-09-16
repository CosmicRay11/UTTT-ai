## Ultimate Tic Tac Toe project

import tkinter as tk

from GameManager import GameManager
from Board import Board
from MCTS_ML import MCTS_ML

import random
import pandas as pd
import cProfile
import numpy as np

import tensorflow as tf
import keras
from keras import layers
from keras.models import Model
from keras import models
from keras.optimizers import Adam

import datetime

import sys, os
OUTPUT = sys.stdout

# Disable
def blockPrint():
    sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
    sys.stdout = OUTPUT


class MCTS_ML_train(MCTS_ML):
    def __init__(self, board, neuralNet=None):
        if neuralNet == None:
            ## make a neural net of the right shape
            pass
        
        MCTS_ML.__init__(self, board, neuralNet)

    ## select moves at weighted randomness for the current player to make, given the current state of the game tree
    def choose_best_move(self):
        children = self.tree.root.children

        total = float(self.tree.root.den)
        weightedProbs = [child.den / total for child in children]
        bestNode = random.choices(children, weights = weightedProbs)[0]
        return bestNode

    def return_policy(self):
        children = self.tree.root.children

        total = float(self.tree.root.den)

        policy = np.zeros((3,3,3,3))
        for child in children:
            x,y,i,j = child.move
            policy[x,y,i,j] += child.den

        policy = policy / total
        policy = Board.flatten(policy)
        return policy
        

def make_net(learningRate):
    input_layer = layers.Input(shape=(9,9), name="BoardInput")
    reshape = layers.core.Reshape((9,9,1))(input_layer)
    conv_1 = layers.Conv2D(128, (3,3), padding='valid', activation='relu', name='conv1')(reshape)
    conv_2 = layers.Conv2D(128, (3,3), padding='valid', activation='relu', name='conv2')(conv_1)
    conv_3 = layers.Conv2D(128, (3,3), padding='valid', activation='relu', name='conv3')(conv_2)

    conv_3_flat = layers.Flatten()(conv_3)

    dense_1 = layers.Dense(512, activation='relu', name='dense1')(conv_3_flat)
    dense_2 = layers.Dense(256, activation='relu', name='dense2')(dense_1)

    pi = layers.Dense(81, activation="softmax", name='pi')(dense_2)
    v = layers.Dense(1, activation="tanh", name='value')(dense_2)

    model = Model(inputs=input_layer, outputs=[pi, v])
    model.compile(loss=['categorical_crossentropy','mean_squared_error'], optimizer=Adam(learningRate))

    return model


def train_nn(nn, states, policies, results):

    states = np.array(states)
    policies = np.array(policies)
    results = np.array(results)

    print(states.shape, policies.shape, results.shape)

    history = nn.fit(states, [policies, results], batch_size=32, epochs=TRAINING_EPOCHS, verbose=0)

    print("loss is", history.history['loss'][-1])

def do_one_move(ai, board):
    lastMove = board.get_last_move()
    ai.update_tree_nodeless(board, lastMove)
    
    for it in range(MCTS_ITERS):
        print(it, "/", MCTS_ITERS)
        ai.consider_moves(board)
    moveNode = ai.choose_best_move()
    move = moveNode.move
    
    policy = ai.return_policy()
    state = board.export()
    
    ai.update_tree(moveNode, board.copy())

    x,y,i,j  = move
    board.make_move(x,y,i,j)

    return state, policy

def play_game(net1, net2):
    b = Board()
    p1 = MCTS_ML_train(b, net1)
    p2 = MCTS_ML_train(b, net2)

    stateList = []
    policyList = []
    resultList = []

    p1Player = b.xstr
    while b.game_state() == b.stateDict["ongoing"]:
        print("move made")
        if b.next_player == p1Player:
            ai = p1
        else:
            ai = p2

        state, policy = do_one_move(ai, b)

        policyList.append(policy)
        stateList.append(state)

    # update the result associated with each state-policy pair to reflect the result of the game
    gameState = b.game_state()
    if gameState == b.stateDict["X win"]:
        result = 1
    elif gameState == b.stateDict["O win"]:
        result = -1
    else:
        result = 0

    for p in policyList:
        resultList.append(result)
        result *= -1

    return stateList, policyList, resultList, gameState

print("libraries imported")

LEARNRATE = 1

input()

path = "data.csv"
cols = ["board", "policy", "end state"]

try:
    data = pd.read_csv(path, index_col = 0)
except FileNotFoundError:
    print("creating new file")
    data = pd.DataFrame(columns = cols)

    data.to_csv(path)



EPOCHS = 100
GAMES_PER_EPOCH = 5
MCTS_ITERS = 400
TRAINING_EPOCHS = 100


net = make_net(LEARNRATE)
net.summary()

board = Board()
import time
s = time.time()
for i in range(100):
    net.predict(board.export().reshape(1,9,9))

t = time.time()
print((t-s) / 100)

for epoch in range(EPOCHS):

    print("Epoch {}".format(epoch + 1))

    net.save('temp.h5')
    oldNet = models.load_model('temp.h5')

    states = []
    policies = []
    results = []

    for game in range(GAMES_PER_EPOCH):
        print("Game {} / {}".format(game+1, GAMES_PER_EPOCH))
        stateList, policyList, resultList, gameState = play_game(net, net)
        

        states += stateList
        results += resultList
        policies += policyList

    train_nn(net, states, policies, results)

    
    


now = datetime.utcnow()
filename = 'tictactoe_MCTS200{}.h5'.format(now)
model_path = os.path.join(save_model_path,filename)
nn.save(model_path)



# cython board is really worth it, 2x speed improvement
