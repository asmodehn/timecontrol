"""
A schedule of expectations
expects have a target date on which they should be satisfied.
learning and loopng will be used in the meantime to maximize learning (ie. minimize intents for expects satisfaction)

At targetdate, unsatisfaction is triggered at a higher level (not in this learning loop).
"""
import asyncio
from collections import OrderedDict
from dataclasses import dataclass, field

import typing
from datetime import datetime, timezone, timedelta

import dpcontracts


@dataclass(frozen=True)
class Expect:  # Note : this is an expected event, with timestamp into the future...
    # todo : support more time representations...
    targetdate: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    focus: asyncio.Event = field(default_factory=asyncio.Event)
    # TODO : now() should probably be a class variable (to be constant and accessible by other classes)

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)

    async def __call__(self):  # Note: This is a learning algorithm !

        await self.focus.wait()   # to be able to do our own scheduling on named tasks

        print(f"target: {self.targetdate} clock: {datetime.now(tz=timezone.utc)}")

        # TODO : loop on expectation =/= result to minimize difference...
        # TODO : a control loop implementation for timer (or a simple Additive increase, multiplicative decrease)

        # rescheudle hte task if delta not small enough...
        # Learning/looping is done by the scheduler, not the "Expect" (keeping data/event-like) asyncio.create_task(self())
        # REMINDER : this is what is passed form higherlevel

        self.focus.clear()  # to block again


class ResultSchedule(Schedule):
    """
       This is a generic log, as a wallclock-indexed intents datastore (immutable scheduled intent can be almost anything).
       It is callable, to execute an intent at the current (wall)clock ( ASAP )
       """
    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self, loop=None):
        self._loop = asyncio.get_event_loop() if loop is None else loop
        self.map = OrderedDict()
        self._tasks = set()  # currently running tasks

    @property
    def first(self):
        first_timestep = list(self.map.keys())[-1]
        return self.map[first_timestep]  # take them all
        # we take the first in the list (we might have multiple results in same timestep)

    @dpcontracts.types()
    def __call__(
            self, focus: timedelta
    ):
        now = datetime.now(tz=timezone.utc)
        # prioritize tasks in the current focused timespan (from now())

        for t in self.map:
            t.focus.set()  # TODO

        return focus  # time slipping but nothign noticeable here...=> pure side effecty.

    def __setitem__(self, name, run: Expect):
        # schedule an event into the future !
        idx=len(self.map.get(name, set()))
        name = name+f'_{idx}'
        # Note : we need a proper set for python semantics (unicity, etc.),
        # but we also want to name its elements (unicity of name).
        # The naming is not used in the program, but a useful information for debugging...
        # => Maybe a specific data struct for this would be useful ?
        t = self._loop.create_task(run())  # eager scheduling : maximize use of available compute power...
        # t.set_name(name) py3.8 only  # A task must be created to give it a name... that schedules it. (maybe asyncio specific ?)
        self.map[name] = self.map.get(name, set()) | {t}

    def __delitem__(self, name):
        self.map.pop(name)

    def __getitem__(self, name):
        return self.map.get(name, set())

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
