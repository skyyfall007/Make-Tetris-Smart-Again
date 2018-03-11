#Author: Boima Massaquoi
#Q-learning example using a matrix representation of a node graph from tutorial : http://mnemstudio.org/path-finding-q-learning-tutorial.htm
#The goal is to get to the state with the highest reward
#the angent will traverse the graph by going from node to node until
#they've reached the node with the highest reward.

import random
import csv


#Define reward table
r =[[-1,-1,-1,-1,0,-1],
    [-1,-1,-1,0,-1,100],
    [-1,-1,-1,0,-1,-1],
    [-1,0,0,-1,0,-1],
    [0,-1,-1,0,-1,100],
    [-1,0,-1,-1,0,100]]

gamma =0.8

#Define q-table filled with 0s 
q = [[0 for x in range(6)]
         for y in range(6)]

n_episodes = 1
n_states = 6

c_state = None
n_state = None
c_action = None

goal = False


states = [n for n in range(n_states)]


#Set initial state to random state
#Set Current state to initial State
#from current state, find action with the highest Q value
#go to next state

while n_episodes >0:
    
    n_episodes-=1
    #sets the current state to a random state int value
    c_state = random.choice(states)
    goal = False
    
    while not goal:
        
        available_actions = []
        # gets the action index(i) and the connection value(e) for all available actions given the current state 
        for i,e in enumerate(r[c_state]):
            if e !=-1:
                available_actions.append(i)
                
        c_action = random.choice(available_actions)

        #update q table with EXPECTED REWARD from NEXT POSSIBLE actions BASED OFF CURRENT state and action
        q[c_state][c_action] = r[c_state][c_action]+gamma * max(q[c_action])
        reward = r[c_state][c_action]
        print(q)
        #print '\t'.join([str(ALPHA), str(EPSILON), str(super_cycles), str(super_reward), str(super_violations)])
        
        if reward >=100:
            goal = True
        else:
            c_state =c_action

with open("tester.csv", "w") as f:               
     writer = csv.writer(f,delimiter=",")
     writer.writerows("1")
     
        
