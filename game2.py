# Author: Brij Malhotra
# Filename: game2.py
# Version: 1
# Purpose: Alien invasion game simulation
# Additional features: Radius bomb, after 5 consecutive hits, the next alien hit, the alien
# and any other aliens around in a 1 block radius (3x3 cell) will be blown up. Winning condition
# feature is nuke bomb that triggers and wipes the entire board when the remaining aliens have a
# cumulative strength that is lesser than that of the player's strength in that turn. Only can nuke
# after first 5 moves so that the simulation doesn't break right at the start with barely any aliens

import random
import re
import sys

# Constants
NUM_BYTES = (1024 ** 2) * 100  # 100MB of characters
HEIGHT = 8
WIDTH = 8
STRENGTH = 9
CELL_WIDTH = 11

# ANSI Colors for console output
ANSI_CYAN = "\033[96m"
ANSI_END = "\033[0m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"

class Alien:
    def __init__(self, board, coords, strength):
        self.board = board
        self.coords = coords
        self.strength = strength
        self.board.addAlien(self)
        self.x = coords[0]
        self.y = coords[1]
        self.squished = False
        self.value = bytearray(NUM_BYTES)  # Each alien takes up a large amount of memory
        self.children = []

    def __str__(self):
        return ANSI_RED + str(self.strength) + ANSI_END

    def doDeath(self):
        # Marks this alien as squished and clears its cell on the board. 
        self.squished = True
        self.board.clearCell(self.coords)

    def doPop(self, strength=1):
        # Reduces the alien's strength; marks it as squished if strength falls below 1.
        self.strength -= strength
        if self.strength < 1:
            self.doDeath()

    def doGrow(self):
        # Randomly increases the alien's strength if it is below the max strength.
        chance = random.randint(0, 9)
        if self.strength < STRENGTH and chance > 7:
            self.strength += 1

    def doTimestep(self):
        # Simulates time steps for the alien
        self.doTravel()
        self.doSpawn()
        self.doGrow()

    def doTravel(self):
        # Randomly moves the alien if possible
        distx = random.randint(-1, 1)
        disty = random.randint(-1, 1)
        newx = self.x + distx
        newy = self.y + disty
        if self.inRange((newx, newy)):
            self.board.moveAlien(self.coords, (newx, newy))
            self.coords = (newx, newy)
    
    def doSpawn(self):
        # Spawns a new alien in an adjacent empty cell 
        emptySpace = self.findEmptySpace()
        neighbor = self.getNeighbor()
        chance = random.randint(0, 9)
        if neighbor is not None and emptySpace is not None and chance > 6:
            child = Alien(self.board, emptySpace, max(1, self.strength - 1))
            self.children.append(child)

    def findEmptySpace(self):
        # Finds an adjacent empty space to the alien for spawning.
        adjacent = [(self.x + 1, self.y + 1), (self.x + 1, self.y), (self.x + 1, self.y - 1),
                    (self.x, self.y + 1), (self.x, self.y - 1), (self.x - 1, self.y - 1),
                    (self.x - 1, self.y), (self.x - 1, self.y + 1)]
        random.shuffle(adjacent)
        for coords in adjacent:
            if self.inRange(coords) and self.board.isEmpty(coords):
               return coords
        return None

    def getNeighbor(self):
        # Finds a random adjacent alien. 
        adjacent = [(self.x + 1, self.y + 1), (self.x + 1, self.y), (self.x + 1, self.y - 1),
                    (self.x, self.y + 1), (self.x, self.y - 1), (self.x - 1, self.y - 1),
                    (self.x - 1, self.y), (self.x - 1, self.y + 1)]
        neighbors = []
        for coords in adjacent:
            if self.inRange(coords):
                neighbor = self.board.getAlien(coords)
                if neighbor is not None:
                    neighbors.append(neighbor)
        if not neighbors:
            return None
        return neighbors[random.randint(0, len(neighbors) - 1)]

    def inRange(self, coords):
        # Error checking of the boundaries
        return 0 <= coords[0] < self.board.width and 0 <= coords[1] < self.board.height

class Board:
    def __init__(self, height, width):
        self.board = [[None for _ in range(width)] for _ in range(height)]
        self.height = height
        self.width = width
        self.player = None  # Reference to the player

    def __str__(self):
        
        string = ""
        for i in range(self.width):
            cells1 = []
            cells2 = []
            for j in range(self.height):
                alien = self.getAlien((i, j))
                cell1 = "|    -     "
                if alien is not None and not alien.squished:
                    cell1 = "|    {0}     ".format(alien)
                cell2 = "| ({0:02d},{1:02d})  ".format(i, j)
                if j == (self.height - 1):
                    cell1 += '|'
                    cell2 += '|'
                cells1.append(cell1)
                cells2.append(cell2)
            string += '-' * ((len(cells1) * CELL_WIDTH) + 1)
            string += '\n'
            for cell in cells1:
                string += cell
            string += '\n'
            for cell in cells2:
                string += cell
            string += '\n'
            if i == (self.width - 1):
                string += '-' * ((len(cells1) * CELL_WIDTH) + 1)
                string += '\n'
        return string

    def addAlien(self, alien):
        # Adds an alien to the board at its current coordinates.
        self.board[alien.coords[0]][alien.coords[1]] = alien

    def clearCell(self, coords):
        # Clears the cell at the given coordinates. 
        self.board[coords[0]][coords[1]] = None

    def doTimestep(self):
        # Time step simulation.
        for i in range(self.width):
            for j in range(self.height):
                alien = self.getAlien((i, j))
                if alien is not None and not alien.squished:
                    alien.doTimestep()

    def getAlien(self, coords):
        # Returns the alien at the given coordinates, or None if empty. 
        return self.board[coords[0]][coords[1]]

    def isEmpty(self, coords=None):
        # Checks if the specified cell or the entire board is empty. 
        if coords is None:
            return all(self.getAlien((i, j)) is None for i in range(self.width) for j in range(self.height))
        else:
            return self.getAlien(coords) is None

    def moveAlien(self, oldCoords, newCoords):
        # Moves an alien from oldCoords to newCoords. 
        if not self.isEmpty(oldCoords) and self.isEmpty(newCoords):
            alien = self.getAlien(oldCoords)
            self.clearCell(oldCoords)
            self.board[newCoords[0]][newCoords[1]] = alien
            alien.x, alien.y = newCoords[0], newCoords[1]

    def squish(self, coords, strength=1):
        # Attempts to squish the alien at the given coordinates. 
        if not (0 <= coords[0] < self.width and 0 <= coords[1] < self.height):
            print("Invalid coordinates. Lose your turn.")
            return -1
        elif self.isEmpty(coords):
            print("Cell is empty. Lose your turn.")
            return -1
        else:
            alien = self.getAlien(coords)
            if alien is not None:
                score = strength if alien.strength > strength else alien.strength
                alien.doPop(strength)
                if score > 0:
                    self.player.consecutive_hits += 1
                    if self.player.consecutive_hits >= 5: # Condition to use the radius bomb feature
                        self.player.trigger_bomb(coords)  # Trigger the radius bomb after 5 hits
                        self.player.consecutive_hits = 0
                else:
                    self.player.consecutive_hits = 0
                return score
        return -1

class Player:
    def __init__(self, board, troops, bombs):
        self.board = board
        self.score = 0
        self.strength = 1
        self.turn = 0
        self.consecutive_hits = 0  # Count of consecutive successful hits

    def __str__(self):
    
        width = self.board.width
        size = (width * CELL_WIDTH) + 1
        string = "TURN: {0}\tSTRENGTH: {1}\tSCORE: ".format(self.turn, self.strength)
        if self.score > 0:
            string += ANSI_GREEN + str(self.score) + ANSI_END
        elif self.score == 0:
            string += str(self.score)
        else:
            string += ANSI_RED + str(self.score) + ANSI_END
        return "{0:^{1}}".format(string, size)

    def doTimestep(self):
        # Updates the player's turn count. 
        self.turn += 1

    def trigger_bomb(self, epicenter):

        # Triggers a radius bomb that affects all aliens within a 1-block radius around the epicenter. 

        bomb_range = range(-1, 2)  # This creates a range from -1 to 1
        affected_cells = [(epicenter[0] + dx, epicenter[1] + dy) for dx in bomb_range for dy in bomb_range
                      if 0 <= epicenter[0] + dx < WIDTH and 0 <= epicenter[1] + dy < HEIGHT]
    
        print(f"Triggering bomb at {epicenter} affecting {len(affected_cells)} cells")
        for (x, y) in affected_cells:
            alien = self.board.getAlien((x, y))
            if alien:
                alien.doDeath()


def printTree(alien, depth=0):

    tree = "{0}({1}):".format(str(alien), depth)
    if len(alien.children) == 0:
        return tree
    else:
        for child in alien.children:
            tree += printTree(child, depth + 1)
    return tree

def printTrees(aliens):

    for alien in aliens:
        tree = printTree(alien)
        print(tree)

def garbage_collect(aliens):

    # Iteratively mark and sweep garbage collection to remove references to squished aliens.

    for root_alien in aliens:
        if root_alien.squished:
            continue  # Skip entirely squished roots early

        stack = [(root_alien, None, 0)]  # Stack holds tuples of (alien, parent, index_in_parent)
        while stack:
            current_alien, parent, idx = stack.pop()

            if current_alien.squished:
                # If current alien is squished, remove it from its parent
                if parent is not None:
                    parent.children[idx] = None
            else:
                # Push children to stack, remember parent and index
                for i, child in enumerate(current_alien.children):
                    stack.append((child, current_alien, i))

        # Filter out and clean squished aliens
        if not root_alien.squished:
            root_alien.children = [child for child in root_alien.children if child is not None]

    # Return all non-squished aliens
    return [alien for alien in aliens if not alien.squished and alien.children or not alien.squished]

def nuke_board(board):
    
    # Clears all aliens from the board. This function represents the nuke effect
    # used when the player's strength is greater than all remaining aliens' strength on the board

    for i in range(board.width):
        for j in range(board.height):
            alien = board.getAlien((i, j))
            if alien:
                alien.doDeath()

if __name__ == "__main__":
    seed = 0
    if len(sys.argv) > 1:
        seed = sum([ord(c) for c in sys.argv[1]])
    random.seed(seed)
    
    aliens = []
    board = Board(HEIGHT, WIDTH)
    player = Player(board, 3, 3)
    board.player = player
    userin = ""
    
    while(userin.upper() != "QUIT" and userin.upper() != "EXIT"):
        if all(not board.isEmpty((x, y)) for x in range(WIDTH) for y in range(HEIGHT)):
            print("Game over! The board is full of aliens.")  # Losing condition
            break
        
        if player.turn > 5:  # Check the winning condition only after 5 turns
            # Calculate the sum of strengths of all non-squished aliens
            alive_aliens = [alien for row in board.board for alien in row if alien is not None and not alien.squished]
            total_alien_strength = sum(alien.strength for alien in alive_aliens)
            
            # Check the winning condition based on the sum of alien strengths
            if total_alien_strength < player.strength:
                print(f"The total strength of remaining aliens ({total_alien_strength}) is less than the player's strength ({player.strength}). You win by nuking the board!")
                nuke_board(board)  # Nuke the board as the win action
                print(board)
                break
        
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        s = random.randint(1, STRENGTH)
        if player.turn == 0:
            s = 5
        if board.isEmpty((x, y)):
            alien = Alien(board, (x, y), s)
            aliens.append(alien)
        
        print(board)
        print(player)
        
        userin = input("Choose a coordinate to attack (x,y): ")
        search = re.search(r"\(?(-?\d+)[, ]+(-?\d+)\)?", userin)
        (userx, usery) = search.groups() if search else (None, None)
        
        if userx is None or usery is None:
            if userin.upper() in ["QUIT", "EXIT"]:
                continue
            elif userin.upper() == "TREES":
                printTrees(aliens)
                continue
            print("Invalid coordinates. Lose your turn.")
        else:
            userx = int(userx)
            usery = int(usery)
            score = board.squish((userx, usery), player.strength)
            if score > 0:
                player.strength += 1 if player.strength < STRENGTH else 0
            elif score <= 0:
                player.strength -= 1 if player.strength > 1 else 0
            player.score += score
        
        board.doTimestep()
        player.doTimestep()
        aliens = garbage_collect(aliens)  # Apply garbage collection after each turn simulation
        
        if board.isEmpty():
            print("You win!")
            break
