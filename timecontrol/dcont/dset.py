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
from pyrsistent import pset, PSet


class DSet():  # TODO : type constructor ? Via decorator/metaclass ??
    """
    It looks like a set, it behaves like a set, but it is not exactly a set
    => it cannot be empty, only itself.

    This is a directed container, with the only direction being time.
    It interface via python init, call and iterator methods.

    It aims to guarantee proper directed container behavior over time dimension (by contrast to the state/space dimension)
    """
    elems: PSet
    sem: asyncio.BoundedSemaphore

    # wrapping task to be able to control execution
    @classmethod
    async def __taskwrap(cls, t, s: asyncio.Semaphore):
        await s.acquire()  # blocking on start, waiting for scheduler's release -> discipline !
        async with s:
            return await t

    #@dpcontracts.require("l must be iterable (state bimonad) and callable (time bimonad)", lambda args:  callable(args.l) and hasattr(args.l, '__next__'))
    def __init__(self, *args):  # container (monadic - space) interface
        # scheduling tasks for computation in background (for time bimonad, later we must be able to get results...)

        # Using Semaphore for runtime synchronization
        self.sem = asyncio.BoundedSemaphore(len(args))

        # assuming enough compute resources # TODO: link that to number of CPUs to allow reschedule...
        # store (logically parallel) tasks (indeterministic compute order at this level)
        # we store task to be able to retrieve them one at a time without blocking control flow.

        # if we have a value, nothing needs to be done
        object.__setattr__(self, 'elems',
                           # we grab the content if it is a dset already (flatten -> implicit state-monadic join)
                           # or we schedule task -once !- if we got a coroutine (run request -> implicit time-comonadic duplicate)
                           # or (just a value) we add it to the elements
                            pset(iterable=(a.elems if isinstance(a, DSet) else
                                           asyncio.create_task(DSet.__taskwrap(a, self.sem)) if inspect.iscoroutine(a) else
                                           a for a in args),
                            pre_size=len(args)
        ))

        super(DSet, self).__init__()

    def __repr__(self):
        """ Using custom representation - randomized distribution in set to limit side-effects"""
        return f"DSet<{repr(set(random.sample(self.elems, len(self.elems))))}>"

    def __str__(self):
        """
        Using python naive representation  - randomized distribution in set to limit side-effects """
        return str(set(random.sample(self.elems, len(self.elems))))

    def __eq__(self, other):
        # exact same data in memory (optim) or same content ( python's set semantics)
        return id(self.elems) == id(other.elems) or set(self.elems) == set(other.elems)  # Note : no need to shuffle/sample here.

    # NOTE: these are not arguments, they are running option, independent from the task to run.
    async def __call__(self, *args, **kwargs):  # run (state-monadic return) + result stream (time-comonadic extract)
        # NOTE : This code actually starts on await (not on __call__ !! coros are internal in asyncio)
        for i in range(1, len(self)):
            self.sem.release()  # releasing all semaphores to start async computation.

        # executing here (after await, not after call ! ) will await on
        # ANY on going computation (guaranteeing overall progress - keeping semantics of "smallest timebox")
        return DSet(*random.sample({await e if isinstance(e, asyncio.Task) else e for e in self.elems}, len(self.elems)))
        # TODO : improve that maybe by doing pyrsistent transform instead of computing the whole set...

    def __iter__(self):  # stream (state-comonadic extract) interface
        # TODO : async to wait for completion ?
        return iter(random.sample(self.elems, len(self.elems)))  # always an element, taken at random, until exhaustion
        # TODO: categorical semantics of exhaustion ??? affine elements + linear types ?

    def __len__(self):
        return len(self.elems) + 1

# TODO : maybe DSet is just an interface (a trait over an Iterable/Callable/Hashable type ??)
# TODO: If we make DSet a type constructor, maybe we can get rid of the semaphore and consider init as the return (instead of call)
# => Time simplicity at the expense of state simplicity


if __name__ == '__main__':
    import time

    async def schedule():
        ds = DSet('a', 'b', 'c')

        assert len(ds) == 4

        for e in ds:
            print(e)

        async def printme(arg):
            print("sleeping a bit...")
            #await asyncio.sleep(1)  # just to test
            print(arg)
            print("Job done !")
            return arg

        df = DSet(printme(arg=42))

        print("print me is scheduled !")

        await asyncio.sleep(1)

        print("lets start the machine !")

        dres = df()

        print("I'm fading out...")

        await asyncio.sleep(2)

        print("what the hmrmrmhmrflfl....")

        await asyncio.sleep(3)

        print("OOPS I feel asleep, nothing happened yet ? ")

        await asyncio.sleep(1)

        print("Lets get the result already !")

        print(await dres)

        # This is needed only if we dont await (block) before
        await asyncio.sleep(1)

        print("Ok onto something else now !")

    asyncio.run(schedule())
