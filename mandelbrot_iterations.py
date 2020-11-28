#!/usr/bin/env python

from time import time
from random import random, uniform, gauss
from math import sin, cos, pi, sqrt
from colorsys import hsv_to_rgb, rgb_to_hsv

import numba
import pygame
from pygame import Vector2 as Vec2
import pygame.gfxdraw as gfx
from pygame.locals import *


SIZE = (1920, 1080)
FPS = 60
BG_COLOR = 0x202324
BG_COLOR = (16, 19, 20)
AXIS = 0xffa500
BULB = (230, 230, 255)
LINE = 0xff00ff
GRAD_SIZE = 5
CAPTION = "Mandelbrot iterations"


def mix(a, b, t):
    return [
            int(a[0] * (1 - t) + b[0] * t),
            int(a[1] * (1 - t) + b[1] * t),
            int(a[2] * (1 - t) + b[2] * t),
        ]

def seq(z0, maxi, bound=4):
    z = z0
    for i in range(maxi):
        yield z
        z = z*z + z0
        if bound and abs(z) > bound:
            break


@numba.njit
def _mandel(px, tl, dx, dy):

    for y in range(SIZE[1]):
        for x in range(SIZE[0]):

            z0 = tl + dx * x + dy * y * 1j
            z = 0
            for i in range(256):
                z = z*z + z0
                if abs(z) > 2000:
                    break
            px[x, y] = sqrt(i) * 16



def mandel(cam):
    s = pygame.Surface(SIZE, depth=8)
    s.set_palette(
            [   mix(BG_COLOR, BULB, x / 256)
                for x in range(256)]
            )

    px = pygame.surfarray.pixels2d(s)
    res = cam.to_complex((1, 1)) - cam.to_complex((0, 0))
    _mandel(px, cam.topleft, res.real, res.imag)

    return s


class Camera:
    def __init__(self, screen_size, complex_center, complex_height):
        self.ssize = screen_size
        self.ccenter = complex_center
        self.cheight = complex_height

    @property
    def cwidth(self):
        return self.cheight * self.ssize[0] / self.ssize[1]

    def to_screen(self, complex):
        c = complex - self.ccenter
        normalized = (c.real / self.cwidth + 0.5, c.imag / self.cheight + 0.5)

        screen = (normalized[0] * self.ssize[0], normalized[1] * self.ssize[1])

        return screen

    def to_complex(self, screen):
        normalized = (screen[0] / self.ssize[0], screen[1] / self.ssize[1])
        c = complex(
                (normalized[0] - 0.5) * self.cwidth + self.ccenter.real,
                (normalized[1] - 0.5) * self.cheight + self.ccenter.imag,
            )

        return c

    @property
    def topleft(self):
        return self.ccenter - complex(self.cwidth, self.cheight) / 2

    @property
    def bottomright(self):
        return self.ccenter + complex(self.cwidth, self.cheight) / 2


def main():
    screen = pygame.display.set_mode(SIZE)
    pygame.display.set_caption(CAPTION)
    clock = pygame.time.Clock()

    camera = Camera(SIZE, complex(-0.75, 0), 2.5)
    mandelbrot_surf = mandel(camera)
    show_mand = False

    done = False
    while not done:

        # Input
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = True
                elif event.key == K_m:
                    show_mand = not show_mand
                else:
                    print(event.key)
            elif event.type == MOUSEBUTTONDOWN:

                mouse = pygame.mouse.get_pos()
                print(mouse, "button:", event.button)

        # Draw

        screen.fill(BG_COLOR)
        if show_mand:
            screen.blit(mandelbrot_surf, (0, 0))
        else:
            screen.fill(BG_COLOR)

        # Axis
        zero = camera.to_screen(0)
        pygame.draw.line(screen, AXIS, (0, zero[1]), (SIZE[0], zero[1]))  # X axis
        pygame.draw.line(screen, AXIS, (zero[0], 0), (zero[0], SIZE[1]))  # Y axis

        tl = camera.topleft
        br = camera.bottomright

        real = tl.real // 0.25 * 0.25
        while real < br.real:
            pos = camera.to_screen(real + 0j)
            if real == int(real):
                mult = 3
            elif 2*real == int(2*real):
                mult = 2
            else:
                mult = 1
            pygame.draw.line(screen, AXIS, (pos[0], pos[1] - GRAD_SIZE*mult), (pos[0], pos[1] + GRAD_SIZE*mult))
            real += 0.25

        imag = tl.imag // 0.25 * 0.25
        while imag < br.imag:
            pos = camera.to_screen(imag * 1j)
            if imag == int(imag):
                mult = 3
            elif 2*imag == int(2*imag):
                mult = 2
            else:
                mult = 1
            g = GRAD_SIZE * mult
            pygame.draw.line(screen, AXIS, (pos[0] - g, pos[1]), (pos[0] + g, pos[1]))
            imag += 0.25

        mouse = camera.to_complex(pygame.mouse.get_pos())

        points = [camera.to_screen(x) for x in seq(mouse, 20, 1000)]
        # print(points)
        pygame.draw.lines(screen, LINE, False, points, )





        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
