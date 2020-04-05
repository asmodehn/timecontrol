from __future__ import annotations

import asyncio
import typing
from collections.abc import MutableMapping

# TODO : type parameter for values (scheduled tasks)


class AgentSchedule(MutableMapping):
    """ A schedule that can run async (no matter the event loop) """

    # TODO : this could be a directed container in "future time" (/vs/ in "~current~ and past time" for the agentloop)
    #  => some algebra on it... time is a linear sequence (* will merge, + could be choice, deterministic or not. => requires a select functor... LATER)
    schedule: typing.Dict[float, typing.Awaitable]

    def __init__(self, schedule):
        self.schedule = schedule

    async def __call__(self, loop, sleeper = asyncio.sleep):
        for t, a in sorted(self.schedule.items(), key=lambda e: e[0]):
            await sleeper(t - loop.time())  # sleep if needed
            await a  # run the coro

    def copy(self):
        return schedule(self.schedule.copy())

    def __getitem__(self, item: float) -> typing.Awaitable:
        # TODO : test slices
        return self.schedule[item]

    def __setitem__(self, key: float, value):
        self.schedule[key] = value

    def __delitem__(self, key):
        self.schedule.pop(key)

    def __iter__(self):
        """ Iterators on keys only (like for usual mappings in python)"""
        for t in sorted(self.schedule.keys()):
            yield t

    def __len__(self):
        return len(self.schedule)

    def __mul__(self, other: AgentSchedule):
        """ Merging two agent schedules.
        Incidently the same semantics as if *running* both in parallel, in one thread with unlimited time,
         as it is managed by python interpreter
        """
        # prevent collision in keys by adding an epsilon in time (we need to keep both actions here)
        colliding=[t for t in other.schedule if t in self.schedule]

        epsilon_time = 0.1  # TODO: somewhere else...

        newsched = self.schedule.copy()

        for t, a in other.schedule.items():
            newt = t
            while newt in newsched.keys():
                # TODO : some kind of randomized backoff ??
                newt += epsilon_time
            newsched[newt] = a

        # merging left over actions
        return schedule(schedule=newsched)


EmptySchedule = AgentSchedule(dict())


def schedule(schedule: typing.MutableMapping=None):
    if schedule:
        if isinstance(schedule, AgentSchedule):
            return schedule
        else:  # another kind of mapping means we should encapsulate it.
            return AgentSchedule(schedule=schedule)
    else:
        return EmptySchedule

