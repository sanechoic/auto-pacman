# myGhostAgents.py

from game import Agent
import math
import numpy as np
import random

class Queue:
    def __init__(self):
        self.items = []
    def isEmpty(self):
        return self.items == []
    def enqueue(self, item):
        self.items.insert(0,item)
    def dequeue(self):
        return self.items.pop()

class team4GhostAgents( Agent ): # defines getAction and getDistribution

    first = True
    list = [['East', (1, 0)], ['South', (0, -1)], ['West', (-1, 0)], ['North', (0, 1)], ['Stop', (0, 0)]]
    ghostStart = []

    def __init__( self, index ):
        self.index = index

    def getAction( self, state ):

        if self.first:
            self.first = False
            self.WallsGrid = state.getWalls()

            self.WallArray = np.zeros((self.WallsGrid.width, self.WallsGrid.height), dtype=bool)
            for x in range(len(self.WallArray)):
                for y in range(len(self.WallArray[1])):
                    if self.WallsGrid[x][y]: self.WallArray[x][y] = True
            self.ghostStart.append(state.getGhostPositions())

        LegalActions = state.getLegalActions(self.index)
        time = state.data.agentStates[self.index].scaredTimer
        pacpos = state.getPacmanPosition()
        ghostpo = [tuple([int(math.floor(state.getGhostPosition(l + 1)[k])) for k in range(2)]) for l in range(len(state.getGhostPositions()))]

        if len(LegalActions) != 1:
            if time > 0: return self.run_home(state, pacpos, ghostpo[self.index-1])
            return self.PacmanTrap(state, self.WallArray, pacpos, ghostpo)
        else: return LegalActions[0]

    def PacmanTrap (self, state, WallArray, pacpos, ghostpo):

        junctions = self.NextJunctions(WallArray, pacpos)
        other = self.index % 2
        route = []

        for x in range (len(junctions)):
           route += self.shortest_path(WallArray, pacpos, junctions[x], junctions[x-1], False)

        if ghostpo[self.index-1] not in junctions:
            for r in route:
                if ghostpo[other] == tuple(r):
                    return self.PTPacman(state, pacpos, ghostpo[self.index-1], ghostpo[other]) #other chasing
            #print self.index, ghostpo[self.index-1], ghostpo[other], junctions, "junctions"
            return self.PTJunctions(state, junctions, ghostpo, pacpos) #go for junctions
        else:
            for r in route:
                if ghostpo[other] == tuple(r):
                    print self.index, ghostpo[self.index-1], pacpos, "other chasing"
                    return self.PTPacman(state, pacpos, ghostpo[self.index-1], ghostpo[other]) #other chasing
            list(junctions).remove(ghostpo[self.index-1])
            return self.PTPacman(state, pacpos, ghostpo[self.index-1], junctions[0])

    def PTJunctions (self, state, junctions, ghostpos, pacpos):

        route = [[[] for k in xrange(len(junctions))] for j in xrange(len(junctions))]
        i = self.index - 1
        o = self.index % 2

        if self.JunctionIdentify(pacpos): pacpos = (0,0)

        for x in range(len(junctions)):
            for y in range(len(junctions)):
                route[x][y] = self.shortest_path(self.WallArray, junctions[y], ghostpos[x], pacpos, self.vectorToDirection(self.list, state, (x+1), 0))     #vectorToDirection(self, list, state, a, rev)

        if len(route) >= 2:
            if len(route[i][0]) + len(route[o][1]) > len(route[i][1]) + len(route[o][0]):
                return self.Return(state, route[i][1])
            else: return self.Return(state, route[i][0])
        return self.Return(state, route[0][0])

    def run_home(self, state, pacpos, ghostpos):

        route = self.shortest_path(self.WallArray, self.ghostStart[self.index - 1][0], ghostpos, pacpos, self.vectorToDirection(self.list, state, self.index, 0))
        if len(route) <= 1:
            return random.choice(state.getLegalActions(self.index))
        return self.Return(state, route)

    def PTPacman (self, state, pacpos, ghostpos, block):

        route = self.shortest_path(self.WallArray, pacpos, ghostpos, block, self.vectorToDirection(self.list, state, self.index, 0))
        return self.Return(state, route)

    def shortest_path(self, WallArray, end, start, block, direction):

        neighbours = Queue()  # queue storing the next positions to explore
        neighbours.enqueue(start)
        counts = np.zeros((len(WallArray), len(WallArray[0])), dtype=int)
        predecessors = np.zeros((counts.shape[0], counts.shape[1], 2), dtype=int)  # 2D array storing the predecessors
        counts[start[0], start[1]] = 1

        if block == start or block == end: block = (0,0)
        if start == end: return [start]
        counts[block[0], block[1]] = 100

        if direction:
            if(start[0]-direction[1], start[1]-direction[0]) != end:
                counts[start[0]-direction[0], start[1]-direction[1]] = 100

        while not neighbours.isEmpty():
            n = neighbours.dequeue()
            if tuple(n) == tuple(end): break  # path found

            for nb in [[n[0] - 1, n[1]], [n[0] + 1, n[1]], [n[0], n[1] - 1], [n[0], n[1] + 1]]:
                if n[0] > 0 and not WallArray[nb[0], nb[1]] and counts[nb[0], nb[1]] == 0:
                    neighbours.enqueue(nb)
                    predecessors[nb[0], nb[1]] = n
                    counts[nb[0], nb[1]] = counts[n[0], n[1]] + 1
        if counts[int(end[0]), int(end[1])] == 0:
            return start
        n = end
        path = []

        while n != start:  # reconstruct the path
            if tuple(n) == tuple(start): break
            path.append(n)
            if len(path)>100:
                return start
            n = predecessors[int(n[0]), int(n[1])].tolist()
        path.append(start)
        return path

    def JunctionIdentify(self, pos):

        connect = 0
        for x in range(4):
            if self.WallsGrid[pos[0] + self.DirCreate(x, 0)][pos[1] + self.DirCreate(x, 1)] == False:
                connect += 1

        if connect >= 3: return True
        else: return False

    def NextJunctions(self, WallArray, start):
        junctions = []
        neighbours = Queue()  # queue storing the next positions to explore
        neighbours.enqueue(start)
        counts = np.zeros((self.WallsGrid.width, self.WallsGrid.height), dtype=int)
        counts[start[0], start[1]] = 1
        while not len(junctions) >= 2:
            if not neighbours.isEmpty():
                n = neighbours.dequeue()
            else: return tuple(junctions)
            if self.JunctionIdentify(n):
                junctions.append(tuple(n))
            if tuple(n) == start or tuple(n) not in junctions:
                for x in range(4):
                    n1 = ((n[0] + self.DirCreate(x, 0)), (n[1] + self.DirCreate(x, 1)))
                    if n[0] > 0 and not WallArray[n1[0], n1[1]] and counts[n1[0], n1[1]] == 0:
                        neighbours.enqueue([n1[0], n1[1]])
                        counts[n1[0], n1[1]] = counts[n[0], n[1]] + 1
        return tuple(junctions)

    def DirCreate(self, x, a):
        return (((x + a) % 2) * ((-1) ** ((x / 2) + 1)))

    def vectorToDirection(self, list, state, a, rev):

        if not rev:
            a = state.data.agentStates[a].getDirection()
        for i in range(len(list)):
            if list[i][rev] == a: return list[i][(rev+1)%2]

    def Return(self, state, route):
        if len(route) > 2:
            if self.vectorToDirection(self.list, state, (route[-2][0] - route[-1][0], route[-2][1] - route[-1][1]), 1) in state.getLegalActions(self.index):
                return self.vectorToDirection(self.list, state, (route[-2][0] - route[-1][0], route[-2][1] - route[-1][1]), 1)
        return random.choice(state.getLegalActions(self.index))