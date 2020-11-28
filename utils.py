# Lot of simple functions that I often use
# And the Vec2 class

from math import sqrt, atan, pi
from colorsys import hsv_to_rgb


# Functions

def v2sum(a, b):
    """Sum two tuples as if the are 2D vectors.  """
    return [a[0] + b[0], a[1] + b[1]]


def hsv_to_RGB(hue, sat, val):
    """Convert a HSV color in range 0-1 to a RGB in range 0-255."""
    color = hsv_to_rgb(hue % 1, sat, val)
    return [int(255*x) for x in color]


def int_to_rgb(col: int):
    b = col & 0xff
    g = col >> 8 & 0xff
    r = col >> 16 & 0xff
    return r, g, b

def contrast(col):
    if isinstance(col, int):
        col = int_to_rgb(col)

    if sum(col) / 3 > 0x80:
        return 0x000000
    else:
        return 0xffffff


def fmt(s, fg=None, bg=None, reset=True):
    """
    Add ANSI escape codes to a string.

    [fg] and [bg] can either be an rgb tuple of integers
        or an index into COLORS.

    If [reset] is False, the colors and any ANSI flags are not cleared.
    """

    flags = ""

    if fg is not None:
        if isinstance(fg, int):
            r, g, b = int_to_rgb(fg)
        else:
            r, g, b = fg
        flags += f"38;2;{r};{g};{b};"

    if bg is not None:
        if isinstance(bg, int):
            r, g, b = int_to_rgb(bg)
        else:
            r, g, b = bg
        flags += f"48;2;{r};{g};{b};"

    flags = flags.strip(";")

    return "\033[" + flags + "m" + s + "\033[m"


# Classes

class Vec2:
    """Simple 2D vector class."""

    __slots__ = ("x", "y")

    def __init__(self, x, y):
        """Simple 2D vector class."""

        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x}, {self.y})"

    def __getitem__(self, index):
        if index:
            return self.y
        return self.x

    def __iter__(self):
        yield self.x
        yield self.y

    def __add__(self, other):
        return Vec2(self.x + other[0], self.y + other[1])

    def __radd__(self, other):
        self.x += other[0]
        self.y += other[1]
        return self

    def __sub__(self, other):
        return Vec2(self.x - other[0], self.y - other[1])

    def __mul__(self, other):
        return Vec2(self.x * other, self.y * other)

    def dist2(self, other):
        """Return the square distance to an other point."""
        return (self.x - other[0]) ** 2 + (self.y - other[1]) ** 2

    def norm2(self):
        return self.x ** 2 + self.y**2

    def norm(self):
        return sqrt(self.x ** 2 + self.y ** 2)

    def normalized(self):
        return self * (1 / self.norm())

    def perp(self):
        """Return a orthogonormal vector."""
        n = self.norm2() ** 0.5
        return Vec2(self.y / n, -self.x / n)

    def angle(self):
        """Return the angle of the vector in radians."""

        if self.x == 0:
            if self.y > 0:
                return pi/2
            elif self.y < 0:
                return -pi/2
            else:
                return 0

        a = atan(self.y / self.x)
        if self.x < 0:
            a = a + pi

        return a

