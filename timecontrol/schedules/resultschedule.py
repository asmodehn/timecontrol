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

from timecontrol.schedules.schedule import Schedule, Intent


@dataclass(frozen=True)
class Expect(Intent):
    expected: typing.Any = None
    # TODO : now() should probably be a class variable (to be constant and accessible by other classes)

    def __init__(self, expected: typing.Any):
        object.__setattr__(self, 'expected', expected)

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)

    def __call__(self, res):  # Note: This is a learning algorithm !
        # Rtrieve result and compare with expectation
        return self.expected - res   # some measure of distance (to be minimized by learner)


class ResultSchedule(Schedule):
    """
       This is a generic log, as a wallclock-indexed intents datastore (immutable scheduled intent can be almost anything).
       It is callable, to execute an intent at the current (wall)clock ( ASAP )
       """
    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self, *expectations: Expect):
        super(ResultSchedule, self).__init__(*expectations)

    @dpcontracts.types()
    def __call__(
            self
    ):
        return super(ResultSchedule, self).__call__()


if __name__ == '__main__':

    i1 = Expect()

    i2 = Expect()

    s = ResultSchedule(i1, i2)

    assert s() == i1

    assert s() == i2