#!/usr/bin/env python
from math import pi
from pathlib import Path

import numpy as np
import pygame
import pygame.gfxdraw
from pygame.locals import *

SIZE = (1500, 800)
FPS = 60
BG_COLOR = 0x202324
CAPTION = Path(__file__).absolute().as_posix()

NB_PENDULUMS = 1000
DT = 0.1
STEPS_PER_FRAME = 1
SCALE = 6
GRAVITY = 1

WHITE = (255, 255, 255)


class Pendulum:
    def __init__(self, number=100):
        self.mass1 = np.ones(number)
        self.mass2 = np.ones(number) / 3
        self.length1 = np.ones(number) * 30
        self.length2 = np.ones(number) * 30
        avg_angle = pi - 0.1
        dev = 0.01
        self.angle1 = np.linspace(avg_angle - dev, avg_angle + dev, number)
        self.angle2 = np.ones(number)
        self.angle_vel1 = np.zeros(number)
        self.angle_vel2 = np.zeros(number)
        self.color = np.linspace(
            (255, 165, 0, 20), WHITE + (20,), number, dtype=np.uint8
        )

    def logic(self):
        for _ in range(STEPS_PER_FRAME):
            self._logic()

    def _logic(self):
        angle_acc_1 = (
            -GRAVITY * (2 * self.mass1 + self.mass2) * np.sin(self.angle1)
            - self.mass2 * GRAVITY * np.sin(self.angle1 - 2 * self.angle2)
            - 2
            * np.sin(self.angle1 - self.angle2)
            * self.mass2
            * (
                self.angle_vel2 ** 2 * self.length2
                + self.angle_vel1 ** 2
                * self.length1
                * np.cos(self.angle1 - self.angle2)
            )
        ) / (
            self.length1
            * (
                2 * self.mass1
                + self.mass2
                - self.mass2 * np.cos(2 * (self.angle1 - self.angle2))
            )
        )

        angle_acc_2 = (
            2
            * (
                np.sin(self.angle1 - self.angle2)
                * (
                    self.angle_vel1 ** 2 * self.length1 * (self.mass1 + self.mass2)
                    + GRAVITY * (self.mass1 + self.mass2) * np.cos(self.angle1)
                    + self.angle_vel2 ** 2
                    * self.length2
                    * self.mass2
                    * np.cos(self.angle1 - self.angle2)
                )
            )
            / (
                self.length2
                * (
                    2 * self.mass1
                    + self.mass2
                    - self.mass2 * np.cos(2 * (self.angle1 - self.angle2))
                )
            )
        )

        self.angle_vel1 += angle_acc_1 * DT
        self.angle_vel2 += angle_acc_2 * DT
        self.angle1 += self.angle_vel1 * DT
        self.angle2 += self.angle_vel2 * DT

    def draw(self, display):
        center = pygame.Vector2(SIZE) / 2
        for a1, a2, l1, l2, color in zip(
            self.angle1, self.angle2, self.length1, self.length2, self.color
        ):
            p1 = center + polar(l1 * SCALE, a1)
            p2 = p1 + polar(l2 * SCALE, a2)

            pygame.gfxdraw.line(display, *vec2int(center), *vec2int(p1), color)
            pygame.gfxdraw.line(display, *vec2int(p1), *vec2int(p2), color)
            # pygame.draw.line(display, (255, 255, 255), center, p1)
            # pygame.draw.line(display, (255, 255, 255), p1, p2)


def vec2int(vec):
    return (int(vec[0]), int(vec[1]))


def polar(length, angle):
    v = pygame.Vector2()
    v.from_polar((length, 90 + angle * 180 / pi))
    return v


def main():
    pygame.init()
    display = pygame.display.set_mode(SIZE)
    pygame.display.set_caption(CAPTION)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 60)

    objects = [Pendulum(NB_PENDULUMS)]

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
        for obj in objects:
            obj.logic()

        # Draw
        display.fill(BG_COLOR)

        for obj in objects:
            obj.draw(display)

        fps = clock.get_fps()
        s = font.render(str(round(fps, 2)), True, WHITE)
        display.blit(s, (5, 5))

        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
