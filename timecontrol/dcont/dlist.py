# A non empty list implemented on top of an functional (immutable) datastructure.
from __future__ import annotations

import asyncio
import inspect
import typing
from collections.abc import Sequence
from copy import copy, deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import dpcontracts
from pyrsistent import pvector, PVector, CheckedPVector
from typeclasses import typeclass

"""
REMINDER : Although we think about time dimension properties, we shouldnt implement time related topics here.
These are left for another module to take care of.

Note, in python
- the state-monadic interface is the class constructor for the instance + tensor operation ('__add__' for sequence/list for instance)
- the state-comonadic interface is the iterator on the instance + tensor operation ('__add__' for sequence/stream for instance)

- the time-monadic interface is the container class to a more "basic"/fast/small data -> data processing is contained in time, with the call() triggering computation
  => tensor operation is 'concatenation' of containers when call concatenate computation
- the time-comonadic interface is an observer on call (iterator on scheduled tasks - async mandatory, profiling, etc.)
  => tensor operation is 'concatenation' of observed computation ('sequenced scheduling') => never idle ! => special noop task (different from sleep that needs to take time !)

=> problem : time scales -> timeframe for computation / compatibility with sleep...

- space dimension : TODO (non local data...) maybe match a state dimension at a higher scale ? ie one localized agent takes care of one type. 
"""

# TODO : typeclass ??
class DList():
    """
    It looks like a list, it behaves like a list, but it is not exactly a list
    => it cannot be empty ! We can always get the root (the origin list !) element

    It is also, like DSet, bimonadic in state:
    >>> three = dlist(1,2,3)  # return
    >>> three
    dlist(1,2,3)

    and join / duplicate are "implicit"

    >>> assert three == dlist(three)

    extract is the usual list index __getitem__ call
    >>> three[2]
    3

    And bimonadic in time-dimension (for __call__ and __next__):

    # return is done via calling (appends to the list if already exists)
    >>> five1 = three(4)(5)
    >>> five2 = three(4,5)

    join/duplicate are "implicit" but rely on python semantics and feel like currying...
    >>> five1
    dlist(1,2,3,4,5)
    >>> five2
    dlist(1,2,3,4,5)

    extract is done via iterating (the usual stream comonad) in python
    >>> two_three = next(three)
    >>> two_three
    dlist(2,3)

    It is also immutable which means if the result of a call is not stored, it will not persist.

    Compared to DSet, here we have a semantic of ordering.

    """
    vector: PVector

    def __init__(self, *args):  # container / monadic interface
        """ Do not use this directly. Use the dlist function provided"""
        # logging stuff
        self.vector = pvector(args)

    def __repr__(self):
        return f"dlist({','.join(str(e) for e in self.vector)})"  # attempting homoiconicity

    def __str__(self):
        return f"[{','.join(str(e) for e in self.vector)}]"  # pretty printing

    def __bool__(self):
        """ Falsy if empty, just like vector"""
        return bool(self.vector)

    def __eq__(self, other: DList):
        """ Stict equality - no duck typing here !
        """
        if type(self) != type(other):
            return False
        # exact same data in memory (optim) or same content
        contentmatch = id(self.vector) == id(other.vector) or self.vector == other.vector
        return contentmatch

    def __call__(self, *elem) -> DList:
        """ appending to the list """
        return dlist(*self.vector, *elem)

    def __getitem__(self, item: int):  # container (comonadic - state) interface: extract
        if item == len(self.vector):
            return EmptyDList
        return self.vector[item]

    def __contains__(self, item):
        """ Contains does not increment focus when checking whats inside ! Useful to check subtype..."""
        return item in self.vector

    def __iter__(self):  # stream / comonadic interface
        return self

    def __next__(self):
        if self.vector:
            # Returning the subcontainer
            return dlist(*self.vector[1::])
        else:
            return EmptyDList

    def __len__(self):
        return len(self.vector) + 1

    # Algebra TODO


# TODO : maybe DList is just an interface (a trait over a type ??)

EmptyDList = DList()


def dlist(*elements):
    if not elements:
        return EmptyDList
    elif len(elements) == 1 and isinstance(elements[0], DList):
        # To get a bimonad we need to encode an implicit join here so that we never need duplicate
        # even if we are semantically compatible.
        return DList(*elements[0].vector)
    else:
        return DList(*elements)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

