#!/usr/bin/env python

"""
A simple graph editor to solve my graph theory exercices.
"""

from time import time
from random import random, uniform, gauss
from math import sin, cos, pi, sqrt
from colorsys import hsv_to_rgb, rgb_to_hsv
from collections import defaultdict

import pygame
from pygame import Vector2 as Vec2
import pygame.gfxdraw as gfx
from pygame.locals import *


SELECT_RANGE = 50
COLORS = [
    (253, 151, 31),
    (166, 226, 46),
    (102, 217, 239),
    (249, 38, 114),
    (174, 129, 255),
    (117, 113, 94),
]

def d(a, b=(0, 0)):
    """Return the distance between two points or the norm of one vector."""
    return sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


class Graph:
    def __init__(self):
        self.points = []
        """Positions of vertices."""
        self.edges = set()
        """Pair of vertex indices, smallest first."""
        self.vertex_colors = []
        self.selected = None
        self.current_color = 0

        self.physics = False
        self.edge_strength = 1

    def __getitem__(self, vertex):
        x, y =  self.points[vertex]
        return int(x), int(y)

    def __len__(self):
        return len(self.points)

    def __delitem__(self, vertex):
        """Remove a vertex and all its edges."""

        del self.vertex_colors[self.selected]
        del self.points[self.selected]

        self.edges = {
                (u - (u > vertex), v - (v > vertex))
                for u, v in self.edges
                if u != vertex and v != vertex
            }

    def add_point(self, pos, connect=False):
        if connect:
            closest = self.closest_point(pos)
        else:
            closest = None

        self.points.append(pos)
        self.vertex_colors.append(self.current_color)

        if closest is not None:
            self.add_edge(closest, len(self.points) - 1)


    def add_edge(self, idx, idy):
        assert 0 <= idx < len(self.points)
        assert 0 <= idy < len(self.points)

        if idx == idy:
            # No self edge
            return

        if idy < idx:
            idx, idy = idy, idx
        self.edges.add((idx, idy))

    def shift_color(self, qte):
        self.current_color += qte
        self.current_color %= len(COLORS)

    def scale_edge_strength(self, factor):
        self.edge_strength *= factor

    def toggle_physics(self):
        self.physics = not self.physics

    def closest_point(self, pos, max_range=None):
        """Return the index of the closest point to [pos]"""
        best = min(range(len(self.points)), key=lambda i: d(self[i], pos), default=None)

        if best is None:
            return None

        if max_range is not None and d(self[best], pos) > max_range:
            return None
        return best

    def mouse_down(self, event):
        if event.button == 4:
            self.shift_color(-1)
        elif event.button == 5:
            self.shift_color(1)
        else:
            self.selected = self.closest_point(event.pos, SELECT_RANGE)

    def mouse_up(self, event):
        if event.button not in (1, 3):
            return

        if self.selected is None:
            self.add_point(event.pos, connect=pygame.key.get_mods() & KMOD_SHIFT)
            return

        closest = self.closest_point(event.pos, SELECT_RANGE)

        if closest is None:
            self.points[self.selected] = event.pos
        elif closest == self.selected:
            if event.button == 3:
                del self[self.selected]
            else:
                self.vertex_colors[self.selected] = self.current_color
        else:
            self.add_edge(closest, self.selected)

        self.selected = None

    def mouse_move(self, event):
        pass

    def select(self, pos):
        self.selected = self.points.index(pos)

    def logic(self):
        if self.physics:
            forces = defaultdict(Vec2)
            for i, p in enumerate(self.points):
                for dj, p2 in enumerate(self.points[i+1:]):
                    j = i + dj + 1
                    d = Vec2(p2) - p  # Vector i->j
                    l = d.length()
                    if (i, j) in self.edges:
                        forces[i] += d * l * self.edge_strength / 100
                        forces[j] -= d * l * self.edge_strength / 100

                    forces[i] -= (200 / l)**2 * d
                    forces[j] += (200 / l)**2 * d
            for i, p in enumerate(self.points):
                self.points[i] += forces[i] / 30

    def shake(self):
        """Move randomly the vertices to untangle the graph."""

        for p in self.points:
            pert = Vec2()
            pert.from_polar((gauss(30, 5), uniform(0, 360)))  #wtf this api
            p += pert

    def draw(self, display):
        # Draw edges below the circles
        for (u, v) in self.edges:
            pygame.draw.line(display, 0xbdface, self[u], self[v], 5)

        # Draw vertices and highlight the first one closest to the mouse
        mouse = pygame.mouse.get_pos()
        highlighted = False
        for p in range(len(self)):
            if p == self.selected:
                color = (255, 42, 42)
            else:
                color = self.color_of(p)

            pos = self[p]

            if d(pos, mouse) < SELECT_RANGE and not highlighted:
                color = pygame.Color(*color) + Color(50, 50, 50)
                highlighted = True

            gfx.filled_circle(display, *pos, 20, color)
            gfx.aacircle(display, *pos, 20, color)

        # draw the colors
        width = SIZE[0] / len(COLORS)
        for i, c in enumerate(COLORS):
            height = 30 if i == self.current_color else 10
            rect = (i * width, SIZE[1] - height, width, height)
            display.fill(c, rect)

    def color_of(self, vertex):
        return COLORS[self.vertex_colors[vertex]]



SIZE = (1500, 800)
FPS = 30
BG_COLOR = 0x202324

def main():
    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    g = Graph()
    objects = [g]

    done = False
    while not done:

        # Input
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    done = True
                elif event.key == K_k:
                    g.scale_edge_strength(1.2)
                elif event.key == K_j:
                    g.scale_edge_strength(0.8)
                elif event.key == K_LEFT:
                    g.shift_color(-1)
                elif event.key == K_RIGHT:
                    g.shift_color(1)
                elif event.key == K_p:
                    g.toggle_physics()
                elif event.key == K_s:
                    g.shake()
                else:
                    print(event.key)
            elif event.type == MOUSEBUTTONDOWN:
                g.mouse_down(event)
            elif event.type == MOUSEBUTTONUP:
                g.mouse_up(event)
            elif event.type == MOUSEMOTION:
                g.mouse_move(event)

        # Logic
        for obj in objects:
            obj.logic()

        # Draw
        screen.fill(BG_COLOR)

        for obj in objects:
            obj.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
