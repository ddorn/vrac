import numpy as np
import matplotlib.pyplot as plt


def weierstrass(xs):
    a = 0.5
    b = 3

    try:
        w = np.zeros(xs.shape)
    except ValueError:
        w = 0

    for i in range(20):
        w += a ** i * np.cos(xs * b ** i)

    return w

def main():
    SIZE = 500
    size = np.array((SIZE, SIZE))

    a = np.array((0, 0))

    x, y = np.indices(size, dtype=float)
    x = (x / size[0]) - 0.5
    y = y / size[1] - 0.5

    bound = 40
    x *= bound
    y *= bound

    def f(x, y):
        scale = 1
        # a = np.maximum(abs(np.sin(scale*x)), 0.0000001)
        # b = np.maximum(abs(np.sin(scale*y)), 0.0000001)
        # return a * np.sin(1 / a) + b * np.sin(1 / b)
        return weierstrass(x) - weierstrass(y) + np.sin(x**2) / 6 + np.cos(y) / 3
        # return weierstrass(weierstrass(x - weierstrass(y)) - weierstrass(y + weierstrass(x)))
        return weierstrass(x * y + x + weierstrass(y + x))

    # dist = abs(x) + abs(y)
    dist = np.sqrt(x**2 + y**2)
    dist += abs(f(*a) - f(x, y))

    dist = dist #// 0.03

    plt.imshow(dist)
    plt.show()


if __name__ == "__main__":
    main()

