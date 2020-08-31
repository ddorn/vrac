from time import time
from random import random, uniform, gauss
from math import sin, cos, pi
from colorsys import hsv_to_rgb, rgb_to_hsv

import pygame
from pygame.locals import *


SIZE = (1500, 800)
FPS = 60
BG_COLOR = 0x202324

def main():
    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    objects = []

    done = False
    while not done:

        # Input
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = True
                else:
                    print(event.key)
            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                print(mouse, "button:", event.button)

        # Logic

        # Draw
        screen.fill(BG_COLOR)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
