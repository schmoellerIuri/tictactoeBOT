# -*- coding: utf-8 -*-
"""
Recriação do Jogo da Velha

@author: Prof. Daniel Cavalcanti Jeronymo
"""

from operator import contains
from threading import Thread
import time
import pygame
    
import sys
import os
import traceback
import random
import numpy as np
import copy

class GameConstants:
    #                  R    G    B
    ColorWhite     = (255, 255, 255)
    ColorBlack     = (  0,   0,   0)
    ColorRed       = (255,   0,   0)
    ColorGreen     = (  0, 255,   0)
    ColorBlue     = (  0, 0,   255)
    ColorDarkGreen = (  0, 155,   0)
    ColorDarkGray  = ( 40,  40,  40)
    BackgroundColor = ColorBlack
    
    screenScale = 1
    screenWidth = screenScale*600
    screenHeight = screenScale*600
    
    # grid size in units
    gridWidth = 3
    gridHeight = 3
    
    # grid size in pixels
    gridMarginSize = 5
    gridCellWidth = screenWidth//gridWidth - 2*gridMarginSize
    gridCellHeight = screenHeight//gridHeight - 2*gridMarginSize
    
    randomSeed = 0
    
    FPS = 30
    
    fontSize = 20

class Node:

    playerToWin = 0
    count = 0
    finalStates = list()
    
    def __init__(self, currentPlayer, currentState = np.zeros((GameConstants.gridHeight, GameConstants.gridWidth))):  
        
        self.state = currentState
        self.currentPlayer = currentPlayer
        self.possibleNextStates = []
        self.winState = False
        self.max = currentPlayer == Node.playerToWin
        self.peso = None
        Node.count += 1

    def SetPlayerToWin(player):
        Node.playerToWin = player

    def InsertNextStates(self):

        if(self.IsFinalState()):
            Node.finalStates.append(self)
            if self.IsWinForPlayer(Node.playerToWin):
                self.peso = 1
                self.winState = True
            elif self.IsDraw():
                self.peso = 0
            else:
                self.peso = -1

            return

        for i in range(3):
            posX = i
            for j in range(3):
                posY = j
                if(self.state[posX][posY] == 0):
                    nextState = copy.deepcopy(self.state)
                    nextState[posX][posY] = self.currentPlayer
                    nextPlayer = 1 if self.currentPlayer == 2 else 2
                    nextNode = Node(nextPlayer, nextState)
                    self.possibleNextStates.append(nextNode)
        
        for state in self.possibleNextStates:
            state.InsertNextStates()

        return 
           
    def IsFinalState(self):   
       return self.IsDraw() or self.WinByColumn() or self.WinByLine() or self.WinByDiagonal()

    def IsWinForPlayer(self, player):
        return self.WinByColumn(player) or self.WinByLine(player) or self.WinByDiagonal(player)

    def WinByColumn(self, winnerPlayer = 0):
        for i in range(3):
            column = set(self.state[:, i])
            
            if winnerPlayer == 0:
                if len(column) == 1 and min(column) != 0:
                    return True
            elif winnerPlayer == 1:
                if len(column) == 1 and min(column) != 0 and contains(column, 1):
                    return True
            elif winnerPlayer == 2:
                if len(column) == 1 and min(column) != 0 and contains(column, 2):
                    return True    
        return False

    def WinByLine(self, winnerPlayer = 0):
        for i in range(3):
            line = set(self.state[i, :])
            if winnerPlayer == 0:
                if len(line) == 1 and min(line) != 0:
                    return True
            elif winnerPlayer == 1:
                if len(line) == 1 and min(line) != 0 and contains(line, 1):
                    return True
            elif winnerPlayer == 2:
                if len(line) == 1 and min(line) != 0 and contains(line, 2):
                    return True
        return False

    def WinByDiagonal(self, winnerPlayer = 0):

        mainDiagonal = set([self.state[i, i] for i in range(3)])
        if winnerPlayer == 0:
            if len(mainDiagonal) == 1 and min(mainDiagonal) != 0:
                return True
        elif winnerPlayer == 1:
            if len(mainDiagonal) == 1 and min(mainDiagonal) != 0 and contains(mainDiagonal, 1):
                return True
        elif winnerPlayer == 2:
            if len(mainDiagonal) == 1 and min(mainDiagonal) != 0 and contains(mainDiagonal, 2):
                return True

        secondDiagonal = set([self.state[-i-1, i] for i in range(3)])
        if winnerPlayer == 0:
            if len(secondDiagonal) == 1 and min(secondDiagonal) != 0:
                return True
        elif winnerPlayer == 1:
            if len(secondDiagonal) == 1 and min(secondDiagonal) != 0 and contains(secondDiagonal, 1):
                return True
        elif winnerPlayer == 2:
            if len(secondDiagonal) == 1 and min(secondDiagonal) != 0 and contains(secondDiagonal, 2):
                return True

        return False    
    
    def IsDraw(self):
        for i in range(3):
            line = self.state[i,:]
            if(min(line) == 0):
                return False           
        return True

    def GetWinStates(self):
        if(self.winState):
            return 1
        elif self.IsFinalState():
            return 0

        total = 0

        for state in self.possibleNextStates:
            total += state.GetWinStates()

        return total

    def GetFinalStates(self):
        if(self.IsFinalState()):
            return 1
    
        total = 0

        for state in self.possibleNextStates:
            total += state.GetFinalStates()

        return total 

    def FindState(self, state):
        for pns in self.possibleNextStates:
            if(np.array_equal(pns.state, state)):
                return pns
        
        return None

class Game:
    class GameState:
        # 0 empty, 1 X, 2 O
        grid = np.zeros((GameConstants.gridHeight, GameConstants.gridWidth))
        currentPlayer = 0
        
    moves = 0

    def __init__(self, helpedPlayer , expectUserInputs=True):
        self.expectUserInputs = expectUserInputs

        self.helpedPlayer = helpedPlayer

        self.currentState = None

        # Game state list - stores a state for each time step (initial state)
        gs = Game.GameState()

        self.states = [gs]
        
        # Determines if simulation is active or not
        self.alive = True
        
        self.currentPlayer = 1
        
        # Journal of inputs by users (stack)
        self.eventJournal = []

    def checkObjectiveState(self, gs):
        # Complete line?
        for i in range(3):
            s = set(gs.grid[i, :])
            if len(s) == 1 and min(s) != 0:
                return s.pop()
            
        # Complete column?
        for i in range(3):
            s = set(gs.grid[:, i])
            if len(s) == 1 and min(s) != 0:
                return s.pop()
            
        # Complete diagonal (main)?
        s = set([gs.grid[i, i] for i in range(3)])
        if len(s) == 1 and min(s) != 0:
            return s.pop()
        
        # Complete diagonal (opposite)?
        s = set([gs.grid[-i-1, i] for i in range(3)])
        if len(s) == 1 and min(s) != 0:
            return s.pop()
            
        # nope, not an objective state
        return 0
    
    
    # Implements a game tick
    # Each call simulates a world step
    def update(self): 
        # Get the current (last) game state
        gs = copy.copy(self.states[-1])

        # Switch player turn
        if gs.currentPlayer == 0:
            gs.currentPlayer = 1

        # If the game is done or there is no event, do nothing
        if (not self.alive or not self.eventJournal) and (gs.currentPlayer == 0 or gs.currentPlayer != Node.playerToWin):
            return
            
        if(gs.currentPlayer != Node.playerToWin):
    
            # Mark the cell clicked by this player if it's an empty cell 
            x,y = self.eventJournal.pop()

            # Check if in bounds
            if x < 0 or y < 0 or x >= GameConstants.gridCellHeight or y >= GameConstants.gridCellWidth:
                return

            # Check if cell is empty
            if gs.grid[x][y] == 0:   
                gs.grid[x][y] = gs.currentPlayer
                Game.moves += 1
                SwitchTurn(gs)
            else: # invalid move
                return
        else:
            if (Game.moves >= 1):
                if not self.currentState.possibleNextStates: return
                posX,posY = melhorJogada(self.currentState)
                gs.grid[posX][posY] = gs.currentPlayer
            else:
                gs.grid[1][1] = gs.currentPlayer
            time.sleep(0.2)
            Game.moves += 1
            SwitchTurn(gs)

        if (Game.moves == 1):
            self.currentState = Node(2,gs.grid)
            self.currentState.InsertNextStates()
            minimax(self.currentState)            
        elif (self.currentState != None):
            self.currentState = self.currentState.FindState(gs.grid)
        
        # Check if end of game
        if self.checkObjectiveState(gs):
            self.alive = False
                
        # Add the new modified state
        self.states += [gs]

def SwitchTurn(gs):
    if gs.currentPlayer == 1:
        gs.currentPlayer = 2
    elif gs.currentPlayer == 2:
        gs.currentPlayer = 1

def drawGrid(screen, game):
    rects = []

    rects = [screen.fill(GameConstants.BackgroundColor)]
    
    # Get the current game state
    gs = game.states[-1]
    grid = gs.grid
 
    # Draw the grid
    for row in range(GameConstants.gridHeight):
        for column in range(GameConstants.gridWidth):
            color = GameConstants.ColorWhite
            
            if grid[row][column] == 1:
                color = GameConstants.ColorRed
            elif grid[row][column] == 2:
                color = GameConstants.ColorBlue
            
            m = GameConstants.gridMarginSize
            w = GameConstants.gridCellWidth
            h = GameConstants.gridCellHeight
            rects += [pygame.draw.rect(screen, color, [(2*m+w) * column + m, (2*m+h) * row + m, w, h])]    
    
    return rects

def draw(screen, font, game):
    rects = []
            
    rects += drawGrid(screen, game)

    return rects

def initialize(playerToWin):
    random.seed(GameConstants.randomSeed)
    pygame.init()
    game = Game(playerToWin)
    font = pygame.font.SysFont('Courier', GameConstants.fontSize)
    fpsClock = pygame.time.Clock()

    # Create display surface
    screen = pygame.display.set_mode((GameConstants.screenWidth, GameConstants.screenHeight), pygame.DOUBLEBUF)
    screen.fill(GameConstants.BackgroundColor)
        
    return screen, font, game, fpsClock

def handleEvents(game):
    #gs = game.states[-1]
    
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONUP:
            pos = pygame.mouse.get_pos()
            
            col = pos[0] // (GameConstants.screenWidth // GameConstants.gridWidth)
            row = pos[1] // (GameConstants.screenHeight // GameConstants.gridHeight)
            #print('clicked cell: {}, {}'.format(cellX, cellY))
            
            # send player action to game
            game.eventJournal.append((row, col))
            
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

def mainGamePlayer(playerToWin):
    try:
        # Initialize pygame and etc.
        screen, font, game, fpsClock = initialize(playerToWin)
              
        # Main game loop
        while game.alive:
            # Handle events
            handleEvents(game)
                    
            # Update world
            game.update()
         
            # Draw this world frame
            rects = draw(screen, font, game)     
            pygame.display.update(rects)
            
            # Delay for required FPS
            fpsClock.tick(GameConstants.FPS)
            
        # close up shop
        pygame.quit()
    except SystemExit:
        pass
    except Exception as e:
        #print("Unexpected error:", sys.exc_info()[0])
        traceback.print_exc(file=sys.stdout)
        pygame.quit()
        #raise Exception from e

class Button:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x,y,100,100)
        self.color = color
        
    def draw(self, screen):
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos) and pygame.mouse.get_pressed()[0] == 1:
            time.sleep(0.1)
            return True
            
        pygame.draw.rect(screen,self.color,self.rect ,border_radius=2)

        return False

def minimax(node):
    if(len(node.possibleNextStates) == 0):
        return

    for psns in node.possibleNextStates:
        minimax(psns)
        if(node.peso == None):
            node.peso = psns.peso
        elif(node.max and psns.peso > node.peso):
            node.peso = psns.peso
        elif(not node.max and psns.peso < node.peso):
            node.peso = psns.peso

def melhorJogada(currentState):
    if currentState == None: return

    melhor = None
    for state in currentState.possibleNextStates:
        if(melhor == None or melhor.peso < state.peso):
            melhor = state

    for i in range(3):
        for j in range(3):
            if currentState.state[i][j] != melhor.state[i][j]:
                return i,j

def decidePlayer():
    pygame.init()
    WIDTH, HEIGHT = 500, 300
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    #pygame.display.set_caption("Hello World!")
    run = True

    blue = Button(100, 100, GameConstants.ColorBlue)
    red = Button(300, 100, GameConstants.ColorRed)

    myfont = pygame.font.SysFont("monospace", 20, bold=True)

    label = myfont.render("Selecione uma cor para jogar", 1, GameConstants.ColorBlack)
    
    while run:
        window.fill(GameConstants.ColorWhite)
         
        blueClicked = blue.draw(window)
        redClicked = red.draw(window)
        window.blit(label, (80, 50))

        pygame.display.flip()
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or blueClicked or redClicked:
                pygame.quit()
                run = False
                break
        #azul selecionado - vermelho é o playerToWin e vice e versa
    if(blueClicked): Node.SetPlayerToWin(1)
    elif(redClicked): Node.SetPlayerToWin(2)
    else: sys.exit("Nenhum player selecionado")

if __name__ == "__main__":
    # Set the working directory (where we expect to find files) to the same
    # directory this .py file is in. You can leave this out of your own
    # code, but it is needed to easily run the examples using "python -m"
    file_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(file_path)

    threadTela = Thread(target = decidePlayer) 

    threadTela.start() 

    threadTela.join()

    mainGamePlayer(Node.playerToWin)