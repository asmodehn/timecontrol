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
import concurrent
import inspect
import random
import time
import typing
from collections.abc import Sequence
from concurrent.futures import Executor
from copy import copy, deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

import dpcontracts
from pyrsistent import pset, PSet



class DSet():  # TODO : type constructor ? Via decorator/metaclass ??
    """
    It looks like a set, it behaves like a set, but it is not exactly a set
    => it cannot be empty, only itself. => this seems to be pointed set ? pointer is taken at random (otherwise use a dmap)

    Also in *time* this is a non-empty list, matching with the realworld time-dimension thourgh python runtime.
    => we can successively access elements of the set.

    This is a directed container, with the only direction being time.
    Interestingly the python runtime semantics seem to indicate that, to be a directed non-empty list in time,
     an empty DSet is always available to be extracted from itself at any time.

    DSet interfaces via python init, call and iterator methods.

    It aims to guarantee proper directed container behavior over time dimension (by contrast to the state/space dimension)
    """
    elems: PSet  # elements for the set. Python semantics may differ and this can contain python runnable definitions.
    # REMINDER : a set has only identity morphisms (skeletal - implicit here), and equal elements are the same (skeletal)
    # Also elements can only be python things, or DSet in our level.
    # Set : Skeletal Small Discrete Category TODO : https://ncatlab.org/nlab/show/set

    executor: Executor

    def __init__(self, *args):  # container (monadic - space) interface
        """ this is the state-monadic return """
        # scheduling tasks for computation in background (for time bimonad, later we must be able to get results...)

        # assuming enough compute resources # TODO: link that to number of CPUs to allow reschedule...
        # store (logically parallel) tasks (indeterministic compute order at this level)
        # we store task to be able to retrieve them one at a time without blocking control flow.

        # if we have a value, nothing needs to be done
        object.__setattr__(self, 'elems',
                           # we grab the content if it is a dset already (flatten -> implicit time-monadic join)
                           # or (just a value) we add it to the elements
                            pset(iterable=(a.elems if isinstance(a, DSet) else
                                           # time synchronization is left to __call__()
                                           # asyncio.create_task(a) if inspect.iscoroutine(a) else
                                           a for a in args),
                            pre_size=len(args)
        ))

        # setting up the executor early (assigning real worldresource)
        self.executor = concurrent.futures.ProcessPoolExecutor()

    def __repr__(self):
        """ Using custom representation - randomized distribution in set to limit side-effects"""
        return f"DSet<{repr(set(self.elems))}>"

    def __str__(self):
        """
        Using python naive representation  - randomized distribution in set to limit side-effects """
        return str(set(self.elems))

    def __eq__(self, other):
        # exact same data in memory (optim) or same content (python's set semantics)
        return id(self.elems) == id(other.elems) or set(self.elems) == set(other.elems)  # Note : no need to shuffle/sample here.

    def __enter__(self):  # TODO : maybe have this optional ??
        """ This interface is an uncontrolled (potentialy remote) computation"""
        # start computing asynchronously (without control)
        return self.executor.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ This is used to terminate the uncontrolled computation """
        # ending computation (without control)
        return self.executor.__exit__(exc_type, exc_val, exc_tb)

    # NOTE: these are not arguments, they are running option, independent from the task to run.
    async def __call__(self, td: datetime =None):  # designing a bit like a "real-time programming interface"
        # TODO : maybe we should be able to pass objects of the *Shapes* category here to allow introspection ? datetime is just a specific shape...
        # TODO : this is a "probe"
        # => Identify shapes with python types ??
        """
        This is the time-monadic return of DSet, embedding computation in the container.
        NOTE : With asyncio, this code actually starts on task scheduling, or on 'await', not on __call__ !!
        coros are internal in asyncio, which has an apparently lazy scheduler.
        BUT THIS IS THE ONLY PLACE in implicit interface where we can await for tasks...

        Note it also takes care of the implicit time-monadic join (on call - computation start)
        and time-comonadic duplicate (on await - computation end) via python operational async semantis,
        But we add an additional limit on computation time, inspired from real-time programming interfaces.
        """
        # default targetdate
        td = datetime.now(timezone.utc) + timedelta(seconds=3) if td is None else td  # defaults to 3 secs timestep

        # initialize computation with raw data (assumed taking no time)
        data = DSet(*{a for a in self.elems if not inspect.iscoroutine(a)})

        # treat coroutines/computation separately
        compute = (a for a in self.elems if inspect.iscoroutine(a))
        results = []
        if compute:
            measured=(0, 0)  # to get maximum initial runtime (average, counter)

            # Start all computations - careful this can explode ! - we have to limit in time to impose control
            while datetime.now(tz=timezone.utc) < td - timedelta(seconds=measured[0]):  # we have to stop before the target date !
                before = time.time()
                try:
                    # One at a time, anyway we have to wait and the control loop cannot return before timestep has ended
                    e = next(compute)
                    # "living" objects in the set are really alive !
                    results.append(await e)  # launching computation here (interleaving in current control flow)
                except StopIteration as si:
                    # TODO: ignore and keep working compute.clear
                    raise
                # TODO: WARNING : functionality compression is key for applicability of this !!!

                # averaging time of process over iterations...
                measured = ((measured[0] * measured[1] + time.time() - before) / (measured[1] + 1), (measured[1] + 1))

        # merge both here using special trick of DSet.__init__
        # This will conserve computation, but also
        return DSet(data.elems.union(set(results)), *compute)  # TODO : This is an "observe" to extract attributes of the category

        # TODO: maybe we just cannot catch in-flight object ? just some statistics ?
        #     # TODO : improve that maybe by doing pyrsistent transform instead of computing the whole set...
        #     # TODO: categorical semantics of exhaustion ??? affine elements + linear types ?

        # TODO maybe some kind of minimal learning here ??

        # executing here (after await, not after call ! ) will await on
        # ANY on going computation (guaranteeing overall progress - keeping semantics of "smallest timebox")
        # TODO : call could be used to verify properties on DSet (Small category ?? -> kitty ?)

    def __contains__(self, item):
        """ Implementing contains, to not have to go through the iteration to check membership """
        return item in self.elems

    def __iter__(self):
        return self

    def __next__(self):
        """ this is the state-comonadic extract of DSet, stream-like. this allows to retrieve/generate the elems
        Note There is no matching with original task inside one timestep - as per set semantics
        The set-monadic return is __init__, storing the computation.

        Note : If you want access to elements distinctively, use a DRecord instead
        but you will have to name them, ie. find a *str* representation for them...
        """
        return DSet(*random.sample(self.elems, 1))  # always an element, taken at random, NO exhaustion ( => linear TT semantics)
        # NOTE : we may return coroutines !

    # NOTE :we do not wan to provide this interface, it would break user's expectations with __len__()
    # def __getitem__(self, item: datetime):
    #     pass

    def __len__(self):
        return len(self.elems)  # we have a len of the number of elements, since we can only retrieve these,
        # NOTE : but we *can* always access one, even if len == 0.

# TODO : maybe DSet is just an interface (a trait over an Iterable/Callable/Hashable (=> DContainer ?) of a type ??)


# The empty DSet, already available and optimally unique in our runtime for id() to match.
EmptyDSet = DSet()


def dset(*args):
    # just because we cannot simpy return an instance from __init__
    # TODO : type constructor (metaclass and return on new ??)
    if not args:
        return EmptyDSet
    else:
        return DSet(*args)


if __name__ == '__main__':

    assert dset() == EmptyDSet

    # A Dice - return monad interface in state & time dimensions - => equi-probabilistic distribution...
    dice = DSet(1, 2, 3, 4, 5, 6)

    assert len(dice) == 6
    # cardinality of the set, but it cannot be empty (there is always something to extract), only itself...

    print(f"Rolling the dice")
    # Observing the dice actually *rolls it* - extract in comonad interface in space & time dimensions -
    # => this feels a bit quantum, statistical approach might be best...
    for s in range(0, 10):
        e = next(iter(dice))
        print(e)

    async def schedule():

        # COMPUTE example

        def add(a, b):  # interpretation of the representation
            return a + b  # implementation of the interpretation

        # Peano inspired
        # Note: all implementation should be in here, not in lower level. no meta lang currently...
        diceS = DSet(1, add(1, 1), add(1, add(1, 1)), add(1, add(1, add(1, 1))),
                     add(1, add(1, add(1, add(1, 1)))), add(1, add(1, add(1, add(1, add(1, 1))))))

        # ONE OR THE OTHER !
        # Contain computation in (atomic - at this scale) time, so we control timeflow here
        # await diceS()

        # ONE OR THE OTHER !
        # Contain computation in (atomic - at this scale) space, so we control stateflow here
        with diceS:
            print("add is running somewhere else!")

            await asyncio.sleep(1)

            print("Lets check the result already !")

        print(f"Rolling the dice")
        for s in range(0, 10):
            e = next(iter(diceS))
            print(e)

        # This might be needed only if we dont await/block before
        await asyncio.sleep(1)

        print("Ok onto something else now !")

    asyncio.run(schedule())
