# myGhostAgents.py

from game import Agent
from game import Actions
from game import Directions
import random
import util

class MyGhostAgent( Agent ):
    def __init__( self, index ):
        self.index = index

    def getAction( self, state ):
        action_list = state.getLegalActions( self.index )
        return action_list[0]

