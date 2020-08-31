from time import time
from random import random, uniform, gauss
from math import sin, cos, pi
from colorsys import hsv_to_rgb, rgb_to_hsv
from typing import List

import pygame
from pygame.locals import *

from sparkles import Sparkle
from utils import *
from vec2 import Vec2


SIZE = (1500, 800)
FPS = 60
BG_COLOR = 0x202324

TOMMY_DENSITY = 3
TOMMY_START = 200
TOMMY_LIFE = 1000
SHOT_DAMMAGE = 50

LEFT = -1
RIGHT = 1

WALL_TOP = 100
WALL_BOTTOM = SIZE[1] - WALL_TOP


pi2 = pi * 2

def fireworks(pos):
    hue = random() if random() < 0.95 else None
    for _ in range(100):
        yield Sparkle.fireworks(pos, hue)


class Entity:
    def __init__(self, pos):
        self.pos = Vec2(*pos)
        self.alive = True

class Player(Entity):
    def __init__(self, pos, side, hue=0.1):
        super().__init__(pos)
        self.side = side  # -1 for left and 1 for right
        self.hue = hue
        self.speed = 0
        self.accel = 0
        self.life = TOMMY_LIFE

        self.going_up = 1

        self.life_bar = LifeBar(self)
        self.shots = []

    def jump(self, direction=None):

        if direction is None:
            self.going_up *= -1
        else:
            self.going_up = direction

        self.accel = self.going_up
        self.speed = 0

    def fire(self):
        self.shots.append(Shot(self.pos, -self.side * 20, self.hue, self.side))

    def collide(self, shots):
        for s in shots:
            if self.pos.dist2(s.pos) < 30**2:
                yield from fireworks(s.pos)
                self.life -= SHOT_DAMMAGE
                s.alive = False

    def update(self) -> List[Sparkle]:
        self.speed += self.accel
        self.pos.y += self.speed

        if self.pos.y <= WALL_TOP:
            self.pos.y = WALL_TOP
            self.speed = 0
            self.accel = 0
        elif self.pos.y >= WALL_BOTTOM:
            self.pos.y = WALL_BOTTOM
            self.speed = 0
            self.accel = 0

        if self.life < 0:
            self.alive = False
            self.life = 0

        for i in range(TOMMY_DENSITY):
            yield Sparkle.tommy(self.pos, self.hue)

        yield from self.life_bar.update()
        for s in self.shots[:]:
            yield from s.update()
            if not s.alive:
                self.shots.remove(s)



class LifeBar:

    def __init__(self, player):
        self.player = player

    def update(self):

        dist = SIZE[0] / 2 * self.player.life / TOMMY_LIFE
        speed = gauss(15, 3)
        # computed so speed=0 when x=dist
        accel = speed ** 2 / (2*dist + speed)

        pos = [SIZE[0] * (self.player.side == RIGHT), gauss(20, 6)]
        pos[0] += speed * self.player.side  # so first time we see it it is on the edge

        for i in range(3):
            yield Sparkle(
                    pos,
                    speed,
                    angle=pi*(self.player.side == RIGHT),
                    accel=accel,
                    color=hsv_to_RGB(gauss(self.player.hue, 0.02), 1, 1),
                    radius=max(0, gauss(6, 1)),
                )


class Enemy(Entity):

    def __init__(self, pos, hue, size):
        """Basic enemy."""
        super().__init__(pos)

        self.hue = hue
        self.size = size

    def update(self):
        self.pos.x -= 5
        if self.pos.x < -100:
            self.alive = False

        for i in range(3):
            color = hsv_to_RGB(gauss(self.hue, 0.05), 1, 1)
            yield Sparkle(
                    self.pos,
                    speed=gauss(6, 0.2),
                    accel=0.2,
                    angle=uniform(0, pi2),
                    angular_accel=0.3 * (random() < 0.5),
                    color=color,
                    gravity_angle=0,
                    gravity=0.08,
                )

class Shot(Entity):
    def __init__(self, pos, speed, hue, player):
        super().__init__(pos)
        self.speed = speed
        self.hue = hue
        self.player = player

    def update(self):
        self.pos.x += self.speed

        if self.pos.x < 0 or self.pos.x > SIZE[0]:
            self.alive = False


        for i in range(2):
            color = hsv_to_RGB(gauss(self.hue, 0.03), 1, 1)
            yield Sparkle(
                    self.pos,
                    speed=gauss(1, 0.1),
                    angle=gauss(pi * (self.player == LEFT), 0.6),
                    accel=0.03,
                    scale=10,
                    color=color,
                )


def main():
    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    player1 = Player((TOMMY_START, WALL_BOTTOM), LEFT, 0.1)
    player2 = Player((SIZE[0] - TOMMY_START, WALL_BOTTOM), RIGHT, 0.55)

    objects = [player1, player2]
    sparkles = []

    done = False
    while not done:

        # Input
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = True

                elif event.key == K_s:
                    player1.jump(1)
                elif event.key == K_w:
                    player1.jump(-1)
                elif event.key == K_SPACE:
                    player1.fire()

                elif event.key == K_j:
                    player2.jump(1)
                elif event.key == K_k:
                    player2.jump(-1)
                elif event.key == K_RETURN:
                    player2.fire()

            elif event.type == MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                print(mouse, "button:", event.button)

        # Logic
        # Spawn enemies
        if random() < 1/FPS and False:
            objects.append(Enemy(
                    (SIZE[0] + 10, uniform(WALL_TOP, WALL_BOTTOM)),
                    hue=0,
                    size=gauss(40, 3)
                ))

        for o in objects[:]:
            sparkles.extend(o.update())
            if not o.alive:
                objects.remove(o)

        sparkles.extend(player1.collide(player2.shots))
        sparkles.extend(player2.collide(player1.shots))


        for s in sparkles[:]:
            s.update()
            if not s.alive:
                sparkles.remove(s)

        # Draw
        screen.fill(BG_COLOR)

        for s in sparkles:
            s.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
