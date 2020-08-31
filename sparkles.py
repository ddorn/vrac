from time import time
from random import random, uniform, gauss
from math import sin, cos, pi
from colorsys import hsv_to_rgb, rgb_to_hsv

import pygame

pi2 = 2*pi

class Sparkle:
    def __init__(self, pos, speed, angle, accel=0.1, angular_accel=0, color=0xffa500, gravity=0, gravity_angle=pi/2, scale=2, radius=None):
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

    def angle_towards(self, angle, rate):
        a = (self.angle - angle + pi) % pi2 - pi
        a *= (1 - rate)

        self.angle = (a + angle ) % pi2

    def update(self, dt=1):
        self.pos = (
                self.pos[0] + dt * self.speed * cos(self.angle),
                self.pos[1] + dt * self.speed * sin(self.angle),  # - 7
            )

        self.speed -= self.accel

        self.angle += self.angular_accel
        self.angle %= 2*pi

        if self.gravity:
            self.angle_towards(self.gravity_angle, self.gravity)

        if self.speed <= 0:
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
        angle = gauss(3*pi/2, pi/3)
        hue = time() / 5 + angle / 50
        color = hsv_to_rgb(hue % 1, 1, 1)
        color = [int(255*x) for x in color]

        return Sparkle(
                pos,
                speed=gauss(7, 2),
                angle=angle,
                accel=max(0, gauss(0.15, 0.03)),
                angular_accel=0,
                color=color,
                gravity=0.10,
                gravity_angle=-pi/2,
            )

    @classmethod
    def swirl(cls, pos):
        """Particls that turn in a water swirl """

        angle = uniform(0, pi2)
        hue = gauss(0.60, 0.04)
        sat = gauss(0.62, 0.06)
        val = gauss(0.32, 0.06)
        color = hsv_to_rgb(hue % 1, sat, val)
        color = [int(255*x) for x in color]

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
        color = [int(255*x) for x in color]

        return Sparkle(
                pos,
                speed=gauss(8, 1),
                accel=0.1,
                angle=angle,
                angular_accel=0,
                color=color,
                gravity=0.00,
                gravity_angle=pi/2,
                scale=gauss(1, 0.1),
            )

    @classmethod
    def tommy(cls, pos, hue=0.1):
        angle = uniform(0, pi2)
        hue = gauss(hue, 0.02)
        color = hsv_to_rgb(hue % 1, 1, 1)
        color = [int(255*x) for x in color]

        return Sparkle(
                pos,
                speed=gauss(8, 1),
                accel=0.8,
                angle=angle,
                angular_accel=0,
                color=color,
                gravity=0.00,
                gravity_angle=pi/2,
                scale=gauss(3, 0.2),
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
    sparkles = []

    done = False
    while not done:

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
                    sparkles.append(Sparkle.fireworks(mouse))
        kind %= len(kinds)

        # Logic

        if fireworks:
            if random() > 0.95:
                pos = random() * SIZE[0], random() * SIZE[1]
                hue = random() if random() < 0.95 else None
                for _ in range(100):
                    sparkles.append(Sparkle.fireworks(pos, hue))

        for _ in range(3):
            sparkles.append(kinds[kind](pygame.mouse.get_pos()))



        for sparkle in sparkles[:]:
            sparkle.update()
            if not sparkle.alive:
                sparkles.remove(sparkle)

        # Draw
        screen.fill(BG_COLOR)
        for sparkle in sparkles:
            sparkle.draw(screen)

        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
