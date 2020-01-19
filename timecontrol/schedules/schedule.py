from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections.abc import MutableMapping

import typing

import dpcontracts
import asyncio

from timecontrol.dcont.dlist import dlist


@dataclass(frozen=True)
class Intent:  # Note : this is an expected event, with timestamp into the future...
    # todo : support more time representations...
    targetdate: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    timecost: typing.Union[int, timedelta] = field(default_factory=lambda: timedelta(seconds=0))  # current timestep scale likely matters here...
    # TODO : now() should probably be a class variable (to be constant and accessible by other classes)

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)


class Schedule:  # TODO: Interface as typeclass ??? Here we are specifying the dlist for intents... use type instance / fmap instead ?
    """
       This is a generic schedule, as a wallclock-indexed intents datastore (immutable scheduled intent can be almost anything).
       It is callable, to execute one or more intent at the current (wall)clock ( ASAP )

       Note : we do not keep track of the past intents (this is likely the job of something at a higher level...
       """

    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self, *intents):
        self.todo = dlist(*intents)

    def __call__(self):
        """ Here call is specific to the schedule (consuming timesteps)"""

        # Extracting next Intent
        next_intent = self[0]

        # consuming it
        next(self)

        # returning next Intent (the caller will find a way to run it appropriately)
        return next_intent

    def __getitem__(self, item):
        return self.todo[item]

    def __iter__(self):
        return self

    def __next__(self):
        """returning ourself after MUTATION
        => This means that we do have the imperative "line-by-line" consumption - expected in python."""
        self.todo = next(self.todo)
        return self

    def __len__(self):
        return self.todo.__len__()


if __name__ == "__main__":
    i1 = Intent()

    i2 = Intent()

    s = Schedule(i1, i2)

    assert s() == i1

    assert s() == i2


