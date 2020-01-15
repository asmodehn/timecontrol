from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections.abc import MutableMapping

import typing

import dpcontracts
import asyncio


@dataclass(frozen=True)
class Intent:  # Note : this is an expected event, with timestamp into the future...
    # todo : support more time representations...
    targetdate: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    timecost: typing.Union[int, timedelta] = field(default_factory=lambda: timedelta(seconds=0))  # current timestep scale likely matters here...
    # TODO : now() should probably be a class variable (to be constant and accessible by other classes)

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)

    async def __call__(self):  # Note: This is a simulation computation algorithm !
        start = datetime.now(tz=timezone.utc)
        # TODO : simulation
        # TODO : maybe a generator that we can stop at a specific time ???
        done = datetime.now(tz=timezone.utc)
        timecost = done - start

        print(f"target: {self.targetdate} clock: {datetime.now(tz=timezone.utc)}")
        if self.targetdate < datetime.now(tz=timezone.utc):
            # if we can afford to wait...
            await asyncio.sleep((self.targetdate - datetime.now(tz=timezone.utc)).total_seconds())

        # return to allow schedule of the actual call
        # Note : simulation-time learning happened here !
        return Intent(targetdate=self.targetdate, timecost=timecost)


class Schedule(MutableMapping):
    """
       This is a generic schedule, as a wallclock-indexed intents datastore (immutable scheduled intent can be almost anything).
       It is callable, to execute one or more intent at the current (wall)clock ( ASAP )

       Note : we do not keep track of the past intents (this is likely the job of something at a higher level...
       """

    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self):
        self.map = OrderedDict()  # Note : A TREE structure ! with ancestry tracked.
        # This is a tree structure indexed by action-time (ie. the datetime where we estimate we "have to" act)
        # => before that, we can run simulations to optimize our action.
        # A time cost is estimated on intents, so it is possible to have sibling nodes
        # => these must be executed before datetimes that are too close to each other to allow simulation.
        # => One must be chosen, but at this level it is "indeterminist" which is chosen (maximize learning up to a point ?)

        self._tasks = set()  # currently running tasks

    @property
    def first(self):
        first_name = list(self.map.keys())[1]  # taking the most ancient intent. one thing at a time.

        return self.map[first_name]  # take them all
        # we take the first in the list (we might have multiple results in same timestep)

    @dpcontracts.types()
    def __call__(
            self, focus
    ):

        # gathering previous intents and returning result to control
        for t in {dt for dt in self._tasks if dt.done()}:
            t.result()
            # TODO : find a way to pass the result to the control...
            self._tasks.remove(t)

        now = datetime.now(tz=timezone.utc)
        # prioritize tasks in the current focused timespan (from now())

        # Run simulation for the scheduled intents in that focus timespan

        next_tasks = [self.first]   # note : comonad here : non empty list => iterator ???
        self.map.pop(next_tasks[-1])
        while next_tasks[-1].targetdate - next_tasks[-1].timecost > now:  # always one in advance...
            next_tasks.append(self.first)  # note : comonad here : non empty list => iterator ???
            self.map.pop(next_tasks[-1])

        # trigger our next tasks
        for t in next_tasks:
            self._tasks = self._tasks | {t}
            t.focus.set()  # TODO

        # TODO : maybe some indicator of load to backpressure control ?
        return focus  # time slipping but trigger only is not noticeable at this scale ...=> pure side effecty.

    def __setitem__(self, targetdate, run: Intent):  # CAREFUL : targetdate must be at the precision of our current timestep here !
        # schedule an event into the future !
        #idx = len(self.map.get(name, set()))
        # name = name+f'_{idx}'
        # Note : we need a proper set for python semantics (unicity, etc.),
        # but we also want to name its elements (unicity of name).
        # The naming is not used in the program, but a useful information for debugging...
        # => Maybe a specific data struct for this would be useful ?
        t = loop.create_task(run())  # eager scheduling : controlling schedule with events...
        # idx = len(self.map.get(name, set()))
        # name = name+f'_{idx}'
        # t.set_name(name)  # py 3.8 only  # BUT means we shouldn't worry about storing names here...

        # We need to compute the proper place in the schedule tree for this intent, based on its estimated timecost
        for td, i in self.map.items():
            # Note : this is a notorious hard problem, just pick an easy and bad solution for now.
            # But think about directed containers...
            parent = i
            #while parent
            # We do not want to add our computation cost to an already big one.
            # => If it overlaps with one existing intent, it is a child of it in the schedule tree (triggering one first, then other in the same timestep)
            if targetdate - i.timecost > td > targetdate:
                # if we fit inside, we are a child (trying to squeeze int he gaps of the big one)
                if targetdate - i.timecost > td - run.timecost > targetdate:
                    pass # TODO
                #else we are a sibling
                else:
                    raise NotImplementedError
            else:
                raise NotImplementedError

        self.map[targetdate] = self.map.get(targetdate, set()) | {t}

    def __delitem__(self, targetdate):
        self.map.pop(targetdate)

    def __getitem__(self, targetdate):
        return self.map.get(targetdate, set())

    def __iter__(self):
        return self.map.__iter__()

    async def __aiter__(self):
        # TODO : wait a bit and return when time has elapsed.
        raise NotImplementedError

    def __len__(self):
        """ Note this is not the total number of task, but rather the number that can be scheduled without dependency"""
        return self.map.__len__()

    def __add__(self, other):
        # TODO : add mergeable functionality
        raise NotImplementedError


# def scheduled(schedule: Schedule):
#     def decorator(cmd):
#         # TODO : nice and clean wrapper
#         def wrapper(*args, **kwargs):
#             scheduled[datetime.now()] = Intent(cmd, args, kwargs)
#         return wrapper
#     return decorator


if __name__ == "__main__":
    import asyncio

    s = Schedule()

    i1 = Intent()

    i2 = Intent()

    s[i1.timestamp] = i1

    s[i2.timestamp] = i2

    loop = asyncio.get_event_loop()

    s(loop=loop)  # passing executor to the scheduler

    loop.run_forever()

