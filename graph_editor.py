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
from graphalama.constants import GREY, WHITESMOKE, DEFAULT, TRANSPARENT
from graphalama.maths import Pos
from pygame import Vector2 as Vec2
import pygame.gfxdraw as gfx
from pygame.locals import *

from graphalama.shadow import NoShadow
from graphalama.widgets import Button, ImageButton, CheckBox
from graphalama.core import WidgetList, Widget
from graphalama.shapes import Padding, Rectangle, RoundedRect

SELECT_RANGE = 50
COLORS = [
    (253, 151, 31),
    (166, 226, 46),
    (102, 217, 239),
    (249, 38, 114),
    (174, 129, 255),
    (117, 113, 94),
]


def clamp(x, mini, maxi):
    if x < mini:
        return mini
    if maxi < x:
        return maxi
    return x


def d(a, b=(0, 0)):
    """Return the distance between two points or the norm of one vector."""
    return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def align_horiz(*widgets: Widget, start=0, interval=2):
    for w in widgets:
        w.pos = (start, w.y)
        start += w.shape.width + interval
    return list(widgets)


class Graph:
    def __init__(self):
        self.points = []
        """Positions of vertices."""
        self.edges = set()
        """Pair of vertex indices, smallest first."""
        self.vertex_colors = []
        self.selected = None
        self.current_color = 0
        self.neightbours = []

        self.physics = False
        self.edge_strength = 1

    def __getitem__(self, vertex):
        x, y = self.points[vertex]
        return int(x), int(y)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    def __len__(self):
        return len(self.points)

    def __delitem__(self, vertex):
        """Remove a vertex and all its edges."""

        del self.vertex_colors[vertex]
        del self.points[vertex]
        del self.neightbours[vertex]

        self.edges = {
            (u - (u > vertex), v - (v > vertex))
            for u, v in self.edges
            if u != vertex and v != vertex
        }

        self.update_neighbours()

    def add_point(self, pos, connect=False):
        if connect:
            closest = self.closest_point(pos)
        else:
            closest = None

        self.points.append(pos)
        self.vertex_colors.append(self.current_color)

        if closest is not None:
            self.neightbours.append({closest})
            self.neightbours[closest].add(len(self) - 1)
            self.add_edge(closest, len(self.points) - 1)
        else:
            self.neightbours.append(set())

    def add_edge(self, idx, idy):
        assert 0 <= idx < len(self.points)
        assert 0 <= idy < len(self.points)

        if idx == idy:
            # No self edge
            return

        if idy < idx:
            idx, idy = idy, idx
        self.edges.add((idx, idy))
        self.neightbours[idx].add(idy)
        self.neightbours[idy].add(idx)

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

    def update_neighbours(self):
        self.neightbours = [
            {x for x in range(len(self)) if self.has_edge(x, p)}
            for p in range(len(self))
        ]

    def has_edge(self, u, v):
        if u > v:
            u, v = v, u
        return (u, v) in self.edges

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
            elif pygame.key.get_mods() & KMOD_SHIFT:
                closest = min(
                    [p for p in range(len(self))
                     if p != self.selected and not self.has_edge(p, self.selected)],
                    key=lambda x: d(self[x], self[self.selected]),
                    default=None
                )
                if closest is not None:
                    self.add_edge(closest, self.selected)
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
        if not self.physics:
            return

        forces = defaultdict(Vec2)
        for i, p in enumerate(self.points):
            for dj, p2 in enumerate(self.points[i + 1:]):
                j = i + dj + 1
                d = Vec2(p2) - p  # Vector i->j
                l = d.length()
                if (i, j) in self.edges:
                    forces[i] += d * self.edge_strength
                    forces[j] -= d * self.edge_strength

                forces[i] -= (200 / l) ** 3 * d
                forces[j] += (200 / l) ** 3 * d

        # Gravity, attract nodes towards the center of the screen
        for i, p in enumerate(self.points):
            forces[i] += Vec2(SIZE) / 2 - p

        for i, p in enumerate(self.points):
            df = forces[i] / 30
            df.x = clamp(df.x, -4, 4)
            df.y = clamp(df.y, -4, 4)
            self.points[i] += df

    def shake(self):
        """Move randomly the vertices to untangle the graph."""

        for p in self.points:
            pert = Vec2()
            pert.from_polar((gauss(50, 10), uniform(0, 360)))  # wtf this api
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

    def tikz(self):
        scale = 0.03  # 33 pixels = 1cm
        t = r"""
\begin{figure}[h!]
\begin{center}
\begin{tikzpicture}[line cap=round,line join=round,>=triangle 45,""" + f"x={scale}cm, y={scale}cm]\n"

        # Draw edges
        for (u, v) in self.edges:
            t += rf"\draw [fill=black] {self[u]} -- {self[v]};" + "\n"

        # Draw vertices
        for vert in self:
            t += rf"\draw [fill=red] {vert} circle (2.5pt);" + "\n"

        t += r"""
\end{tikzpicture}
\end{center}
\caption{A nice graph}
\end{figure}
        """

        print(t)
        pygame.scrap.init()
        pygame.scrap.put(SCRAP_TEXT, t.encode())

        return t

    def clean_exterior(self):
        """Remove all the points not in the screen rectangle."""
        i = len(self) - 1
        while i != -1:
            x, y = self[i]
            if not (0 <= x < SIZE[0] and 0 <= y < SIZE[1]):
                del self[i]
            i -= 1

    def clean(self):
        """Remove all points"""
        self.points = []
        self.vertex_colors = []
        self.edges = set()
        self.selected = None

    def shuffle(self):
        self.points = [
            (uniform(0, SIZE[0]), uniform(0, SIZE[1]))
            for _ in self.points
        ]


SIZE = (1500, 800)
FPS = 30
BG_COLOR = 0x202324


def main():
    pygame.init()
    pygame.display.set_caption("Graph editor")
    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    g = Graph()
    objects = [g]

    button = lambda txt, func, color: Button(txt, func, (10, 10), RoundedRect(border=1, padding=6), color=COLORS[color],
                                             bg_color=(69, 69, 69), border_color=COLORS[color])
    widgets = WidgetList(align_horiz(
        button("Copy Tikz", g.tikz, 0),
        button("Toggle physics", g.toggle_physics, 1),
        button("Clean invisible", g.clean_exterior, 2),
        button("Empty graph", g.clean, 3),
        button("Shuffle", g.shuffle, 4),
        start=10,
        interval=10,
    ))

    done = False
    while not done:
        dt = clock.tick(FPS) / 1000.0  # in seconds

        # Input
        for event in pygame.event.get():
            if event.type == QUIT:
                done = True
            elif widgets.update(event):
                pass
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
                elif event.key == K_t:
                    tikz = g.tikz()
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
        widgets.render(screen)

        pygame.display.update()


if __name__ == "__main__":
    main()
