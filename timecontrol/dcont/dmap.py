"""
In hte spirit of Directed containers as bimonad, a Set doesnt make much sense.

However given our current perspective on multi dimensionality, one dimension is time.
When our concept of past and future time intersect with the present, a Set is a useful simple concept
that can still be made a bimonad, regarding the present-time interval.

It is similar to a DList container, and cannot be empty, but :
 - elements must be unique
 - there is no order semantics from the outside point of view
 - name can be added to retrieve elements from the set

This is useful to represent an ongoing set of computation (looking inward at the smallest possible timeframe)
"""

# A non empty set implemented on top of an functional (immutable) datastructure.
from __future__ import annotations

import asyncio
import inspect
import random
import typing
from collections.abc import Sequence
from copy import copy, deepcopy
from dataclasses import dataclass

import dpcontracts
from pyrsistent import pmap, PMap

from timecontrol.dcont.dset import DSet

from asyncio import AbstractEventLoop

# TODO : maybe use a DClass as a pointed set (with the instance being the set - type -  element)
class DMap(DSet):  # This is a specialization in python semantics only, inheritance is likely appropriate here.
    """
    A DMap behaves like a non-empty list (in the directed container sense) in time,
     but as a usual set in state-dimension.
    We try to keep the python interface separated between the state-dimension (python "data")
     and the time dimension (python "callable")

    It is the same as the DSet, except that here the objects of the set matter and are *named*.
    The name (as string) can be thought as the representation of a higher level thing.
    The variable name (as python atribute name) can be tought of as its interpretation in python.

    """
    # elems is inherited from set, and store the arguments passed without name...
    named_elems: PMap

    def __init__(self, *args, **kwargs):  # container (monadic - space) interface

        # building unnamed set part first
        super(DMap, self).__init__(*args)

        object.__setattr__(self, 'named_elems',
                           # we grab the content if it is a dset already (flatten -> implicit time-monadic join)
                           # or (just a value) we add it to the elements
                           pmap(initial=kwargs,  # Note : no special case here for collapsing collections
                                # if names are passed, we likely do NOT want to collapse (cf tree structure)
                                # Use the *args interface for collapsing trees"  => requires representation of composition
                                pre_size=len(kwargs)
                                ))

    def __getitem__(self, item: str):  # container (monadic - space) interface
        """
        Because elements of the set are named we can access them
        """
        if not item:  # No name given:
            # TODO : give one at random (next / sample semantic) or give the empty record ?
            return EmptyDMap
        return self.named_elems[item]

    def __repr__(self):
        """ Using custom representation - randomized distribution in set to limit side-effects"""
        return f"DMap<{{repr(dict(self.named_element))}}>"

    def __str__(self):
        """
        Using python naive representation  - randomized distribution in set to limit side-effects """
        return str(dict(self.named_elems))

    def __eq__(self, other):
        # exact same data in memory (optim) or same content (python's set semantics)
        return super(DMap, self).__eq__(other) and (
                id(self.named_elems) == id(other.named_elems) or set(self.named_elems) == set(other.named_elems)
        )

    def __iter__(self):
        return self

    def __next__(self):
        """ this is the state-comonadic extract of DMap, stream-like. this allows to retrieve/generate the elems
        Note There is no matching with original task inside one timestep - as per set semantics
        The set-monadic return is __init__, storing the computation.
        """
        #Note : we conserve the semantics of DSet(), just adding the name to it.
        named_elem = random.sample(self.named_elems.items(), 1)
        return DMap(**{n: e for n, e in named_elem})  # always an element, taken at random, NO exhaustion ( => linear TT semantics)
        # NOTE : we may return coroutines !


# The empty DSet, already available and optimally unique in our runtime for id() to match.
EmptyDMap = DMap()


def dmap(**kwargs):
    # just because we cannot simply return an instance from __init__
    # TODO : type constructor (metaclass and return on new ??)
    if not kwargs:
        return EmptyDMap
    else:
        return DMap(**kwargs)


if __name__ == '__main__':

    # DATA example

    dice = DMap(one=1, two=2, three=3, four=4, five=5, six=6)
    # We separate clearly but simply the python representation('four')
    #  of the interpretation of a higher level (name of an element of the 'dl' set)
    # With the implementation (4) of that representation in python (dl['four'])

    print(f"Cardinality: {len(dice)}")

    assert dice[""] is EmptyDMap

    assert dice["one"] == 1

    # cardinality of the set, but it cannot be empty (there is always something to extract), only itself...

    # Observing the dice actually *rolls it* - extract in comonad interface in space & time dimensions -
    # => this feels a bit quantum/statistical...
    for s in range(0, 10):
        e = next(iter(dice))
        print(e)

    async def schedule():
        # COMPUTE example

        def add(a, b):  # interpretation of the representation
            return a+ b  # implementation of the interpretation

        # Peano inspired
        # Note: all implementation should be in here, not in lower level. no meta lang currently...
        diceR = DMap(one=add(0,1), two=add(1,1), three=add(1,add(1,1)), four=add(1, add(1, add(1,1))), five=add(1, add(1, add(1, add(1,1)))), six=add(1, add(1, add(1, add(1, add(1,1))))))

        # ONE OR THE OTHER !
        # Contain computation in (atomic - at this scale) time, so we control timeflow here
        # await diceS()

        # ONE OR THE OTHER !
        # Contain computation in (atomic - at this scale) space, so we control stateflow here
        with diceR:
            print("add is running somewhere else!")

            await asyncio.sleep(1)

            print("Lets check the result already !")

        print(f"Rolling the dice")
        for s in range(0, 10):
            e = next(iter(diceR))
            print(e)

        # This might be needed only if we dont await/block before
        await asyncio.sleep(1)

        print("Ok onto something else now !")

    asyncio.run(schedule())


