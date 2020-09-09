from time import time
from random import random, uniform, gauss
from math import sin, cos, pi
from colorsys import hsv_to_rgb, rgb_to_hsv

import pygame
from utils import *

pi2 = 2 * pi


class Sparkle:
    def __init__(self, pos, speed, angle, accel=0.1, angular_accel=0, color=0xffa500, gravity=0, gravity_angle=pi / 2,
            scale=2, radius=None, vel_bias=(0,0)):
        self.pos = pos
        self.speed = speed
        self.angle = angle
        self.alive = True
        self.accel = accel
        self.angular_accel = angular_accel
        self.color = color
        self.gravity = gravity
        self.gravity_angle = gravity_angle
        self.scale = scale
        self.radius = radius  # If set, radius is constant (overrides scale)
        self.vel_bias = vel_bias

    def __repr__(self):
        return f"<Sparkle({self.pos}, speed={self.speed})>"

    def angle_towards(self, angle, rate):
        a = (self.angle - angle + pi) % pi2 - pi
        a *= (1 - rate)

        self.angle = (a + angle) % pi2

    def update(self, dt=1):
        self.pos = (
            self.pos[0] + dt * (self.speed * cos(self.angle) + self.vel_bias[0]),
            self.pos[1] + dt * (self.speed * sin(self.angle) + self.vel_bias[1]),
        )

        self.speed -= self.accel

        self.angle += self.angular_accel
        self.angle %= 2 * pi

        if self.gravity:
            self.angle_towards(self.gravity_angle, self.gravity)

        if self.speed <= 0:
            self.alive = False

        if self.pos[0] < -50 or self.pos[0] > 10000 or self.pos[1] < -50 or self.pos[1] > 10000:
            # Out of screen
            self.alive = False

    def draw(self, screen):

        if self.radius is not None:
            radius = self.radius
        else:
            radius = self.scale * self.speed

        pygame.draw.circle(
            screen,
            self.color,
            (int(self.pos[0]), int(self.pos[1])),
            int(radius),
        )

    @classmethod
    def fire(cls, pos):
        angle = gauss(3 * pi / 2, pi / 3)
        hue = time() / 5 + angle / 50
        color = hsv_to_rgb(hue % 1, 1, 1)
        color = [int(255 * x) for x in color]

        return Sparkle(
            pos,
            speed=gauss(7, 2),
            angle=angle,
            accel=max(0, gauss(0.15, 0.03)),
            angular_accel=0,
            color=color,
            gravity=0.10,
            gravity_angle=-pi / 2,
        )

    @classmethod
    def swirl(cls, pos):
        """Particls that turn in a water swirl """

        angle = uniform(0, pi2)
        hue = gauss(0.60, 0.04)
        sat = gauss(0.62, 0.06)
        val = gauss(0.32, 0.06)
        color = hsv_to_rgb(hue % 1, sat, val)
        color = [int(255 * x) for x in color]

        speed = gauss(7, 2)

        return Sparkle(
            pos,
            speed=speed,
            angle=angle,
            accel=0.15,
            angular_accel=speed / 100,
            color=color,
        )

    @classmethod
    def fireworks(cls, pos, hue=None):
        """Fireworks distribution. If hue is set, only particles of approx this hue."""

        angle = uniform(0, pi2)
        if hue is None:
            hue = angle / pi2
        else:
            hue = gauss(hue, 0.03)
        color = hsv_to_rgb(hue % 1, 1, 1)
        color = [int(255 * x) for x in color]

        return Sparkle(
            pos,
            speed=gauss(8, 1),
            accel=0.1,
            angle=angle,
            angular_accel=0,
            color=color,
            gravity=0.00,
            gravity_angle=pi / 2,
            scale=gauss(1, 0.1),
        )

    @classmethod
    def tommy(cls, pos, hue=0.1):
        angle = uniform(0, pi2)
        hue = gauss(hue, 0.02)
        color = hsv_to_rgb(hue % 1, 1, 1)
        color = [int(255 * x) for x in color]

        return Sparkle(
            pos,
            speed=gauss(8, 1),
            accel=0.8,
            angle=angle,
            angular_accel=0,
            color=color,
            gravity=0.00,
            gravity_angle=pi / 2,
            scale=gauss(3, 0.2),
        )


class Fountain:
    def update(self):
        yield from []


class LambdaFountain:
    """A Particle emitter that repeatedly call a function generating one particle"""

    def __init__(self, func, density=1):
        self.func = func
        self.density = density

    def update(self):
        for i in range(self.density):
            yield self.func()


class LineFountain(Fountain):
    """A particle emitter in straight line."""

    def __init__(self, start, end, speed, hue, width):
        """Sparkle Fountain between :start: and :end:."""
        Fountain.__init__(self)

        self.start = Vec2(*start)
        self.end = Vec2(*end)
        self.speed = speed
        self.hue = hue
        self.width = width

    def update(self):
        direc = self.end - self.start
        start = self.start + direc.perp() * gauss(0, self.width / 3)
        accel = self.speed ** 2 / (2 * direc.norm() + self.speed)

        yield Sparkle(
            start,
            speed=self.speed,
            angle=direc.angle(),
            accel=accel,
            color=hsv_to_RGB(gauss(self.hue, 0.02), 1, 1),
            scale=max(0, gauss(self.width / 30, self.width / 200))
        )


def main():
    SIZE = (1500, 800)
    FPS = 60
    BG_COLOR = 0x202324

    screen = pygame.display.set_mode(SIZE)
    clock = pygame.time.Clock()

    kind = -1
    kinds = [Sparkle.fire, Sparkle.swirl, Sparkle.fireworks, Sparkle.tommy]

    fireworks = True
    sparkles = set()

    segments = [
        # W
        ((317, 605), (103, 291)),
        ((280, 630), (539, 204)),
        ((544, 593), (363, 179)),
        ((529, 602), (768, 165)),
        # I
        ((832, 598), (857, 277)),
        # N
        ((984, 595), (1030, 231)),
        ((1016, 207), (1230, 607)),
        ((1228, 632), (1364, 266)),
    ]

    fountains = [LineFountain(a, b, 10, 0.1, 50) for a, b in segments]

    frame = 0
    start = time()
    done = False
    while not done:
        frame += 1

        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    done = True
                elif event.key == pygame.K_f:
                    fireworks = not fireworks
                elif event.key == pygame.K_j:
                    kind -= 1
                elif event.key == pygame.K_k:
                    kind += 1
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                for _ in range(100):
                    sparkles.add(Sparkle.fireworks(mouse))

                if event.button == 1:
                    print(mouse, ", ", end='')
                else:
                    print(mouse)

        kind %= len(kinds)

        # Logic

        if fireworks:
            if random() > 0.2:
                pos = random() * SIZE[0], random() * SIZE[1]
                hue = random() if random() < 0.95 else None
                for _ in range(100):
                    sparkles.add(Sparkle.fireworks(pos, hue))

        for _ in range(3):
            sparkles.add(kinds[kind](pygame.mouse.get_pos()))

        for f in fountains:
            sparkles.update(f.update())

        to_remove = set()
        for s in sparkles:
            s.update()
            if not s.alive:
                to_remove.add(s)
        sparkles.difference_update(to_remove)

        # Draw
        screen.fill(BG_COLOR)
        for sparkle in sparkles:
            sparkle.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

        if frame > 60 * 10:
            break

    duration = time() - start
    print(f"Duration: {duration}, FPS: {frame / duration}")


if __name__ == "__main__":
    main()
