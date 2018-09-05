# myPacmanAgents.py

import game
import math
import numpy as np

class Queue:
    def __init__(self):
        self.items = []
    def isEmpty(self):
        return self.items == []
    def enqueue(self, item):
        self.items.insert(0,item)
    def dequeue(self):
        return self.items.pop()

class team4PacmanAgents(game.Agent):

    first = True # allows us to do some operations on the first iteration only
    ticksfood = 0 # counts the number iterations
    ticksCapsules = 0
    list = [['East', (1, 0)], ['South', (0, -1)], ['West', (-1, 0)], ['North', (0, 1)], ['Stop', (0, 0)]] # used to convert directions into movement vectors

    def getAction(self, state):

        if self.first:
            self.first = False
            self.WallsGrid = state.getWalls()

            self.WallArray = np.zeros((self.WallsGrid.width, self.WallsGrid.height), dtype=bool) # create boolean array of walls from Grid
            for x in range(len(self.WallArray)):
                for y in range(len(self.WallArray[1])):
                    if self.WallsGrid[x][y]: self.WallArray[x][y] = True  # Where[x][y] in the Grid is True, [x[y] in the array will also be true

        pacpos = state.getPacmanPosition()
        ghostpos = [tuple([int(math.floor(state.getGhostPosition(l+1)[k])) for k in range(2)]) for l in range(len(state.getGhostPositions()))] #creates a tuple of ghost positions using rounded values so that BFS does not introduce errors
        time = [state.getGhostState(k + 1).scaredTimer for k in range(len(ghostpos))] # time for which ghost is scared
        capsules = state.getCapsules()

        if capsules == []: self.ticksfood += 1 # starts counting iterations after all capsules have been eaten to increase the point potential of food


        if time[0] != 0 or time[1] != 0:
            self.ticksCapsules +=1
            return self.ghostChase(self.WallArray, state, time, ghostpos, capsules, pacpos) #if either ghost is scared, initiate ghost chasing function
        else:
            self.ticksCapsules +=1
            return self.Collect(self.WallArray, ghostpos, state, capsules, pacpos) # initiate function to collect Capsules and Food

    def ghostChase(self, WallArray, state, time, ghostpos, capsules, pacpos):  # shouldn't eat cpasules while timer is on

        routes = [self.shortest_path_block(WallArray, ghostpos[k], pacpos, capsules) for k in range(2)] # whilst ghosts are scared, we do not want to eat any more capsules, so capsules are set as the "block"
                                                                                                                # otherwise we are simply finding the shortest path to the ghost

        if time[0] > 0 and time[1] == 0: # if ghost 1 is scared and ghost 2 is not
            if len(routes[1]) < 5: return self.Collect(WallArray, ghostpos, state, capsules, pacpos)  # if ghost 2 is not within a distance of 5 moves
            else: return self.Return(state, routes[0]) # Chase Ghost 1

        if time[1] > 0 and time[0] == 0: # if ghost 2 is scared and ghost 1 is not
            if len(routes[0]) < 5: return self.Collect(WallArray, ghostpos, state, capsules, pacpos)  # if ghost 1 is not within a distance of 5 moves
            else: return self.Return(state, routes[1]) # Chase Ghost 2

        if time[0] > 0 and time[1] > 0: # if both ghosts are scared
            if len(routes[0]) < len(routes[1]): return self.Return(state, routes[0])  # Chase the closest ghost
            else: return self.Return(state, routes[1])  # Same distance away so it doesn't matter which

    def Collect(self, WallArray, ghostpos, state, capsules, pacpos):

        countsYX = self.PointPotential(WallArray, ghostpos, state, capsules) # create of map of the point potential
        it = 0 # counts number of route search iterations

        for x in capsules:
            if set(self.NextJunctions(WallArray, x)) == set(self.NextJunctions(WallArray, pacpos)):
                return self.Return(state, self.shortest_path_block(WallArray, x, pacpos, None))  #If Pacman shares a junction with a capsule, then he should head for the capsule regardless

        while it <= countsYX.max(): # While the number of iterations is lower than the maximum point potential
            bestPos = [] # list of locations of maximum point potential
            for i in np.argwhere(countsYX == (countsYX.max() - it)): bestPos.append(tuple(i)) # adding locations of highest point potentials to list

            if bestPos:
                for x in bestPos:
                    route = self.shortest_path_block(WallArray, x, pacpos, ghostpos) #find the shortest route to each point in bestPos
                    if len(route) >= 2:
                        if ghostpos[0] != route[-2] and ghostpos[1] != route[-2]:
                            return self.Return(state, route) #if the next move will not take us directly into a ghost then do that move
            it += 1 # if all the possible routes will take us into a ghost, we must search the point of next highest potential until we find a route
        return "Stop"  # if we have searched from max point to zero then we must give up ;(

    def PointPotential(self, WallArray, ghostpos, state, capsules):

        neighbours = [Queue() for i in range(len(ghostpos))]
        counts = [np.zeros((len(WallArray), len(WallArray[0])), dtype=int) for i in range(len(ghostpos))]
        predecessors = [np.zeros((len(WallArray), len(WallArray[0]), 2), dtype=int) for i in range(len(ghostpos))]

        for i in range(len(ghostpos)):
            neighbours[i].enqueue(ghostpos[i])
            counts[i][ghostpos[i]] =1
            while not neighbours[i].isEmpty():
                n = neighbours[i].dequeue()
                for nb in [[n[0] - 1, n[1]], [n[0] + 1, n[1]], [n[0], n[1] - 1], [n[0], n[1] + 1]]:
                    if n[0] > 0 and not WallArray[nb[0], nb[1]] and counts[i][nb[0], nb[1]] == 0:
                        neighbours[i].enqueue(nb)
                        predecessors[i][nb[0], nb[1]] = n
                        counts[i][nb[0], nb[1]] = counts[i][n[0], n[1]] + 1  #adds 1 for every move it would take a ghost to reach a particular location. Therefore the further from the ghosts, the higher the point potential

        countsYX = counts[0] + counts[1] # creates a map of areas of maximum point potential by adding the number of moves it would take both ghosts to reach a point

        for x in range(len(countsYX)):
            for y in range(len(countsYX[0])):
                if state.hasFood(x, y):
                    if capsules: countsYX[x][y] += 2 # fine tunes point potential map by adding value where food is present
                    else:
                        pacpos = state.getPacmanPosition()
                        countsYX[x][y] += (self.ticksfood + 5) + len(self.shortest_path_block(self.WallArray, (x, y), ghostpos[0], None)) #if there are no capsules, food becomes increasingly important, especially food that is far away from ghosts
                        countsYX[self.NextFood(self.WallArray, pacpos, state)[0][0]][self.NextFood(self.WallArray, pacpos, state)[0][1]] += 3
                if (x,y) in capsules:
                    countsYX[x][y] += 30 # fine tunes point potential map by adding value where capsules is present
                    if capsules != []:
                        countsYX[capsules[0][0]][capsules[0][1]] += self.ticksCapsules
        return countsYX # returns adjusted point potential map

    def shortest_path_block(self, WallArray, end, start, block):

        neighbours = Queue()  # queue storing the next positions to explore
        neighbours.enqueue(start)
        counts = np.zeros((len(WallArray), len(WallArray[0])), dtype=int)
        predecessors = np.zeros((counts.shape[0], counts.shape[1], 2), dtype=int)  # 2D array storing the predecessors
        counts[start[0], start[1]] = 1

        if block != None:
            if block == start: return [start]
            if end in block: return [start]
            if start == end: return [start]
            for b in block:
                counts[b[0], b[1]] = 100  # creates a "block" which will stop a route with the block from being considered

        while not neighbours.isEmpty():
            n = neighbours.dequeue()
            if tuple(n) == end: break  # path found

            for nb in [[n[0] - 1, n[1]], [n[0] + 1, n[1]], [n[0], n[1] - 1], [n[0], n[1] + 1]]:
                if n[0] > 0 and not WallArray[nb[0], nb[1]] and counts[nb[0], nb[1]] == 0:
                    neighbours.enqueue(nb)
                    predecessors[nb[0], nb[1]] = n
                    counts[nb[0], nb[1]] = counts[n[0], n[1]] + 1

        if counts[end[0], end[1]] == 0: return []  # path not found

        n = end
        path = []

        while n != start:
            if tuple(n) == start: break
            path.append(n)
            n = predecessors[n[0], n[1]].tolist()
        path.append(start)
        return path

    def vectorToDirection(self, list, state, a, rev):

        if not rev: # select whether you are going from Vector to Direction or Direction to Vector
            a = state.data.agentStates[self.index].getDirection() # get direction of agent
        for i in range(len(list)): # uses list of paired vectors and directions
            if list[i][rev] == a: return list[i][(rev+1)%2] # returns vector or direction based on what you put in

    def JunctionIdentify(self, WallArray, pos):

       connect = 0  # number of connections to a path
       for x in range(4):
           if WallArray[pos[0] + self.DirCreate(x, 0)][pos[1] + self.DirCreate(x, 1)] == False:
               connect += 1 # add one for each connection a point has to a path

       if connect >= 3: return True # if a point has more than threee connections then it must be a junction
       return False

    def DirCreate(self, x, a):
        return (((x + a) % 2) * ((-1) ** ((x / 2) + 1))) # looks through all adjacent points for each point

    def NextJunctions(self, WallArray, start):
        junctions = []
        neighbours = Queue()  # queue storing the next positions to explore
        neighbours.enqueue(start)
        counts = np.zeros((self.WallsGrid.width, self.WallsGrid.height), dtype=int)
        counts[start[0], start[1]] = 1
        while not len(junctions) >= 2: # searches for the closest two junctions
            if not neighbours.isEmpty():
                n = neighbours.dequeue()
            else:
                return tuple(junctions)
            if self.JunctionIdentify(WallArray, n): # identifies whether a point is a junction
                junctions.append(tuple(n))
            if tuple(n) == start or tuple(n) not in junctions:
                for x in range(4):
                    n1 = ((n[0] + self.DirCreate(x, 0)), (n[1] + self.DirCreate(x, 1))) # searches thorugh neighbours of a point
                    if n[0] > 0 and not WallArray[n1[0], n1[1]] and counts[n1[0], n1[1]] == 0:
                        neighbours.enqueue([n1[0], n1[1]])
                        counts[n1[0], n1[1]] = counts[n[0], n[1]] + 1
        return tuple(junctions)

    def Return(self, state, route):
        if len(route) >= 2:
            if self.vectorToDirection(self.list, state, (route[-2][0] - route[-1][0], route[-2][1] - route[-1][1]), 1) in state.getLegalActions(0): # check if direction is legal
                return self.vectorToDirection(self.list, state, (route[-2][0] - route[-1][0], route[-2][1] - route[-1][1]), 1) # return vector between the starting position and the next position in the route as a direction
        return "Stop"

    def NextFood(self, WallArray, start, state):
        food = [start]
        compare = ()
        neighbours = Queue()  # queue storing the next positions to explore
        neighbours.enqueue(start)
        counts = np.zeros((self.WallsGrid.width, self.WallsGrid.height), dtype=int)
        counts[start[0], start[1]] = 1
        while compare != (-1, 0) or (0, -1) or (1, 0) or (0, 1) or start:
            if compare == (-1, 0) or compare == (0, -1) or compare == (1, 0) or compare == (0, 1) or compare == start:
                break
            if len(food) > 1:
                if start in food:
                    food.remove(start)
                else:
                    break
            else:
                compare = (food[-1][0] - start[0], food[-1][1] - start[1])
                n = neighbours.dequeue()
                if state.hasFood(n[0], n[1]):
                    food.insert(0, (n))
                if n not in food or n[0] == start[0] and n[1] == start[1]:
                    for x in range(4):
                        n1 = ((n[0] + self.DirCreate(x, 0)), (n[1] + self.DirCreate(x, 1)))
                        if n[0] > 0 and not WallArray[n1[0], n1[1]] and counts[n1[0], n1[1]] == 0:
                            neighbours.enqueue([n1[0], n1[1]])
                            counts[n1[0], n1[1]] = counts[n[0], n[1]] + 1

        return food
