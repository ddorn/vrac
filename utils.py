# Lot of simple functions that I often use
# And the Vec2 class

from colorsys import hsv_to_rgb


# Functions

def v2sum(a, b):
    """Sum two tuples as if the are 2D vectors.  """
    return [a[0] + b[0], a[1] + b[1]]


def hsv_to_RGB(hue, sat, val):
    """Convert a HSV color in range 0-1 to a RGB in range 0-255."""
    color = hsv_to_rgb(hue % 1, sat, val)
    return [int(255*x) for x in color]

# Classes

class Vec2:
    """Simple 2D vector class."""

    __slots__ = ("x", "y")

    def __init__(self, x, y):
        """Simple 2D vector class."""

        self.x = x
        self.y = y

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

    def __mul__(self, other):
        return Vec2(self.x * other, self.y * other)

    def dist2(self, other):
        """Return the square distance to an other point."""
        return (self.x - other[0]) ** 2 + (self.y - other[1]) ** 2

