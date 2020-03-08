from __future__ import annotations

import time
from datetime import datetime, timedelta, MAXYEAR, MINYEAR
from enum import Enum

import typing


# defining a time-point type ( restriction : > epoch, etc.)
timep = int

# defining a time-delta type (diff restriction and properties
timed = int


class TimeInterval:
    """
    A time interval is a couple of timep.

    We rely on this representation to base everything on interval (for simple yet safe real-world correspondance)
    a time delta is considered an idea, an abstraction. we want to remain imperative / practical
    and keep the code directly related to the real world, python style, for easy maintenance.
    """

    # Note : critical semantic difference between countinterval and timeinterval.
    # For count, since it can only increase, the start is the locally certain count.
    #  and stop is the uncertain possible max count. it will converge somewhere inside itself.
    # For time, since it can only increase, but we can only rely our local clock, start is the past timestamp declared,
    #  and stop is the locally measured (certain max) of the event.
    start: timep
    stop: timep

    @property
    def delta(self) -> timed:
        return self.stop - self.start

    @property
    def median(self) -> timep:
        return self.start + (self.stop - self.start) // 2

    def __init__(self, start: timep = None, stop: timep = None):
        if start > stop:  # invert if needed to keep usual interval semantics
            self.start = stop
        else:
            self.stop = start
        self.start = start
        self.stop = stop

    def __repr__(self):
        return f"{repr(self.start)}..{repr(self.stop)}"

    def __str__(self):
        return f"{str(self.start)}..{str(self.stop)}"

    # Allen's Interval Algebra: https://en.wikipedia.org/wiki/Allen%27s_interval_algebra
    def __eq__(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self.start == self.stop == other
        return self.start == other.start and self.stop == other.stop

    def __hash__(self):
        return hash((self.start, self.stop))

    def after(self, other: typing.Union[timep,TimeInterval]):
        if isinstance(other, timep):
            return self.start > other
        return self.start > other.stop

    def before(self, other: typing.Union[timep,TimeInterval]):
        if isinstance(other, timep):
            return self.stop < other
        return self.stop < other.start

    def __lt__(self, other: TimeInterval):
        return self.before(other)

    def __gt__(self, other: TimeInterval):
        return self.after(other)

    def meets(self, other: typing.Union[timep,TimeInterval]):
        if isinstance(other, timep):
            return other == self.stop
        return self.stop == other.start

    def meets_inv(self, other: typing.Union[timep,TimeInterval]):
        if isinstance(other, timep):
            return self.start == other
        return self.start == other.stop

    def overlaps(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            # ?? False for now (simplest boolean semantics)
            return  False # TODO : what ? fallback on another relation ? which one ?
        return self.start < other.start < self.stop < other.stop

    def overlaps_inv(self, other:  typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            # ?? False for now (simplest boolean semantics)
            return False  # TODO : what ? fallback on another relation ? which one ?
        return other.start < self.start < other.stop < self.stop

    def starts(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self == other  # fallback on equality
        return self.start == other.start and self.stop < other.stop

    def starts_inv(self, other:  typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self.start == other  # lower bound equality sufficient
        return self.start == other.start and self.stop > other.stop

    def during(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return False  # not possible ?? TODO : what about equality ?
        return other.start < self.start and self.stop < other.stop

    def during_inv(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self.start < other < self.stop
        return self.start < other.start and other.stop < self.stop

    def __contains__(self, item: typing.Union[timep, TimeInterval]):
        return self.during_inv(item)

    def finishes(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self == other # fallback on equality
        return self.stop == other.stop and self.start > other.start

    def finishes_inv(self, other: typing.Union[timep, TimeInterval]):
        if isinstance(other, timep):
            return self.stop == other  # higher bound equality sufficient
        return self.stop == other.stop and self.start < other.start


# TODO : conversion to int slices for time.time() based timing

# TODO : there is an equivalent representation with start and duration => how to support it here ?
def timeinterval(start: timep = None, stop: timep=None) -> TimeInterval:
    """
    A time slice with a [now..future] bias on creation
    :param start: start of the interval (lower bound)
    :param stop: end of the interval (upperbound)
    :return:
    """
    # sensible defaults
    # Not the timep type is appropriate to describe time interval from now to infinite.
    # TimeInterval needs to be BOUND on both sides, somehow.
    if start is None:
        start = time.time_ns()
    if stop is None:
        stop = time.time_ns()

    return TimeInterval(start=start, stop=stop)


if __name__ == '__main__':

    now = time.time_ns()

    t1 = timeinterval(now, stop=now + 1000)
    t2 = timeinterval(now, stop=now + 2000)

    assert not t2 in t1
    assert t1.starts(t2)
    assert not t1.finishes(t2)




