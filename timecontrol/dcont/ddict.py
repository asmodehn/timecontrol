from __future__ import annotations

# A directed tree as a dict with special properties
# IDEA : logic on string, similar to object attributes in python : '.' separator for child name
# => each node label correspond to a subtree.
# OR maybe with a different denotation, like ';' as diagrammatic order for morphisms in category theory...
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Hashable

from pyrsistent import pmap, PMap, typing


class DDict:  # TODO : rename DTree. more explicit. Or even Zipper ??? (cf Huet)
    """
    It looks like a dict, it behaves like a dict, but it is not exactly a dict
    => it is a tree and cannot be empty !

    It is used to store some *representation* of a scheduled computation to run in the future.
    The tree structure helps us to match the semantics of the interpreted and current language

    Each element of the tree is a data (in whatever representation decided elsewhere).
    The node index is the pointer to that representation.
     As such it can represent the composition of functions in python via a dict collection.
     Sibling have no special time semantics (can be any kind of execution strategy).
     However we want to stick to categorical semantics :
      - siblings (product) means both data exists (in state) but not in time (concurrency - a choice must be made to progress)
      - in one node we can have a tuple (product) meaning that both data exist in state and in time (parallelism).

    => We must have separate interface for state and time manipulation of this structure.
    State : the usual mapping interface (
    Time : The stream/iterator interface as a comonad in time (to match python time semantics).
      If there ever is a monad/container semantic, it would be __call()__

    """
    map: PMap
    def __init__(self, **kwargs):  # container / monadic interface
        """ Do not use this directly. Use the ddict function provided"""
        self.map = pmap(kwargs)

    def __repr__(self):
        return f"{repr(self.map)}"

    def __str__(self):
        return f"{str(dict(self.map))}"

    def __eq__(self, other: DDict):
        """ Stict equality - no duck typing here !
        """
        if type(self) != type(other):
            return False
        # exact same data in memory (optim) or same content
        contentmatch = id(self.map) == id(other.map) or self.map == other.map
        return contentmatch

    # NOTE : Probably we do not need the call implementation here.
    #  We do not need any specific time semantics represented in state
    #  => scheduling one thing at a time will be done elsewhere.
    #
    # We are at the intermediate level, and we do not need to implement any time related feature directly in here...
    # def __call__(self, *args, **kwargs):
    #     pass

    def __getitem__(self, item: str):  # container (comonadic - state) interface
        if item not in self.map.keys():
            return EmptyDDict
        return self.map[item]  # TODO : a way to get into the Tree structure...

    def __contains__(self, item):
        """ Contains does not increment focus when checking whats inside ! Useful to check subtype..."""
        return item in self.map.values()

    def __iter__(self):  # stream / comonadic interface
        return self

    def __next__(self):
        if self.map.keys():
            choice = random.sample(self.map.keys(), 1)[0]  # TODO : allow parameterizing the random choice here...
            resval = self.map[choice]
            return ddict(**{resval: EmptyDDict})  # Note : hte val becomes hte key....
        else:
            return EmptyDDict

    def __len__(self):
        """ returns the breadth size of the tree """
        return len(self.map)

    # Algebra TODO


# TODO : maybe DList is just an interface (a trait over a type ??)

EmptyDDict = DDict()


# TODO : seems ddct needs some kind of correspondance between keys and values, to be able to access leaf nodes that are the empty tree...
# => hashalbe values ??? python representation ?? generic string representation ???


def emptyddict(value):
    pass

def ddict(**children):
    if not children:
        return "<", EmptyDDict
    elif len(children) == 1:
        key, val = next(children.items())
        if isinstance(val, DDict):
            # To get a bimonad we need to encode an implicit join here so that we never need duplicate
            # even if we are semantically compatible.
            return key, DDict(**val.map)  # consuming the key (and returning it)
        else:
            return ">", DDict(**children)
    else:
        return ">", DDict(**children)


# - storing scheduled computation (refering to 'tasks' by time constraints - 'box' - each node in the tree / maybe matches timescales concept... TODO : Time Interval Logic / TLA+ !)

# Unifying these data structure is probably not trivial (bigraph?).
