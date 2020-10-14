#!/usr/bin/env python

"""
This is a test to see how I could make a map editor with properties that could be set.
It means that I can understand the arguments needed to construct object in an intelligent
way. This is an attempt to make it only with annotations. We'll see how it goes.

Minimum python version: 3.8
"""

from pprint import pprint
import typing
from typing import Literal
from enum import Enum


# Maybe a metaclass will be required
class BaseMeta(type):
    def __repr__(self):
        return f"<{self.__name__}>"

    def args(self):
        return self.__init__.__annotations__


class BaseObject(metaclass=BaseMeta):
    """The base object from which all editor-placeble objects should inherit."""

    def __init__(self, pos):
        # I chose that all objects must have a position, it has always be the case for me
        # And simplifies this aspect.
        self.pos = pos

    def __repr__(self):
        x = [ f"{n}={v!r}" for n, v in self.__dict__.items() ]
        return f"{self.__class__.__name__}({', '.join(x)})"

# Some exemple object I could have in a project
# This is the code I would like to write, and the editor should autoatically know
# How to save, load and define them.
class Dir(Enum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3


class Boost(BaseObject):
    def __init__(self, pos, direction: Literal["up", "down"]):
    # def __init__(self, pos, direction: Dir):
        super().__init__(pos)
        self.direction = direction


class Tree(BaseObject):
    def __init__(self, pos):
        super().__init__(pos)


class Spikes(BaseObject):
    def __init__(self, pos, damage: int):
        super().__init__(pos)
        self.damage = damage

class NPC(BaseObject):
    def __init__(self, pos, name: str):
        super().__init__(pos)
        self.name = name



# Editor definition

class Editor:
    def __init__(self):
        # Note that this way, object must be all defined before the editor is instanciated
        self.objs = BaseObject.__subclasses__()

    def add(self, id, pos=(0, 0)):
        cl = self.objs[id % len(self.objs)]

        kw = {}

        for arg, ann in cl.args().items():
            kw[arg] = self.prompt(arg, ann)

        return cl(pos, **kw)

    def prompt(self, arg, ann):

        if type(ann) == typing._GenericAlias and ann.__origin__ == Literal:
            for i, a in enumerate(ann.__args__):
                print(" ", i, ":", a)
            r = int(input("  literal id: "))
            return ann.__args__[r]

        elif issubclass(ann, Enum):
            for e in ann:
                print(e)
            r = input(f"{ann.__name__}.")
            return ann[r]
        else:
            r = input(f"Value for {arg} ({ann.__name__}): ")

        return ann(r)


eddy = Editor()

for i, o in enumerate(eddy.objs):
    print(i, o)


try:
    while 1:
        print(eddy.add(int(input("kind: "))))
except KeyboardInterrupt:
    pass




# for cl in BaseObject.__subclasses__():
#     print(cl, cl.__init__.__annotations__)
#     print(cl, cl.__init__.__defaults__)

