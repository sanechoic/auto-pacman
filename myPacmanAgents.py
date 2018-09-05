# myPacmanAgents.py

from pacman import Directions
from game import Agent
import random
import game
import util

class MyPacmanAgent(game.Agent):

    def getAction(self, state):
        return Directions.STOP


