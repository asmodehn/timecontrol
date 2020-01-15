from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import MutableMapping

import typing

import dpcontracts
import asyncio

"""
A Schedule of intents
intents have a targetdate to start getting into effect

"""


@dataclass(frozen=True)
class CallIntent:  # Note : this is an expected event, with timestamp into the future...
    # todo : support more time representations...
    targetdate: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # TODO : now() should probably be a class variable (to be constant and accessible by other classes)

    actual: typing.Callable  # representing the thing we intent to experiment by calling it
    simulation: typing.Any = field(default_factory=dict)  # representing a SIMULATION of the thing that we intent to experiment by calling it

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)

    async def __call__(self):  # Note: This is a simulation algorithm !
        print(f"target: {self.targetdate} clock: {datetime.now(tz=timezone.utc)}")

        self.success = self.simulation()


class CallSchedule(MutableMapping):
    """
       This is a generic log, as a wallclock-indexed intents datastore (immutable scheduled intent can be almost anything).
       It is callable, to execute an intent at the current (wall)clock ( ASAP )
       """

    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self):
        self.map = OrderedDict()  # A TREE structure. Indexed by name, but also has a second ordering by priority (ancestry)
        self._tasks = set()  # currently running tasks

    @property
    def first(self):
        first_timestep = list(self.map.keys())[1]  # taking the most ancient intent

        # heuristic to return only ONE child of the current node  -> CHOICE !
        # reference : https://en.wikipedia.org/wiki/B*
        # We rely on the result of the simulation done by the intent (same computation, lower "scale")
        return self.map[first_timestep]  # take them all

        # Note : calling first again (after completion of one task of the intent schedule tree) will bring another one (we have extra allocated time)
        # => the tree node having a sibling is an indeterminist "and" (categorical product)
        # => the tree node having


    @dpcontracts.types()
    def __call__(
            self
    ):
        now = datetime.now(tz=timezone.utc)
        # prioritize tasks in the current focused timespan (from now())

        for t in self.first:
            # TODO : heuristic to prioritize tasks

            t.focus.set()  # TODO

        return focus  # time slipping but nothign noticeable here...=> pure side effecty.


    def __popper(self):
        # asynchronously pops intent out of the list when they are satisfied.
        pass  # TODO

    def __setitem__(self, timestamp, run: CallIntent):
        # schedule an event into the future !
        self.map[timestamp] = self.map.get(timestamp, set()) | {run}

    def __delitem__(self, timestamp):
        self.map.pop(timestamp)

    def __getitem__(self, timestamp):
        return self.map.get(timestamp, set())

    def __iter__(self):
        return self.map.__iter__()

    async def __aiter__(self):
        # TODO : wait a bit and return when time has elapsed.
        raise NotImplementedError

    def __len__(self):
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

    i1 = CallIntent()

    i2 = CallIntent()

    s[i1.timestamp] = i1

    s[i2.timestamp] = i2

    loop = asyncio.get_event_loop()

    s(loop=loop)  # passing executor to the scheduler

    loop.run_forever()

