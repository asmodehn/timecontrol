from __future__ import annotations
from datetime import datetime, timedelta, MAXYEAR, MINYEAR
from enum import Enum

import typing

from collections import namedtuple
from typing import TypeVar

# For now : specific time span:

week = timedelta(weeks=1)
day = timedelta(days=1)
hour = timedelta(hours=1)
minute = timedelta(minutes=1)
second = timedelta(seconds=1)
millisecond = timedelta(milliseconds=1)
microsecond = timedelta(microseconds=1)


class CountInterval:
    """
    A time interval is a couple of timedate (timedelta is deduced).

    We rely on this representation to base everything on interval (for simple yet safe real-world correspondance)
    a time delta is considered an idea, an abstraction. we want to remain imperative / practical
    and keep the code directly related to the real world, python style, for easy maintenance.
    """

    start: int
    stop: int

    @property
    def delta(self) -> int:
        return self.stop - self.start

    @property
    def median(self) -> int:
        return self.start + (self.stop - self.start) // 2

    def __init__(self, start: int = None, stop: int = None):
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
    def __eq__(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.start == self.stop == other
        return self.start == other.start and self.stop == other.stop

    def __hash__(self):
        return hash((self.start, self.stop))

    def __int__(self) -> int:  # conversion to int => take middle (note it depends on current notion of distribution...)
        # Note : we should try to keep conversion explicit to avoid problems
        return (self.start + self.stop) // 2
        # TODO : we want to be able to use interval as ints when needed, to match the core language
        #  The opposite, using ints as interval, is much more tricky without going into full low level python changes
        #  => LATER maybe...
        # Alternative is to design a python extension / language that works,
        # at the lower level with intervals and distributions...

    def after(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.start > other
        return self.start > other.stop

    def before(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.stop < other
        return self.stop < other.start

    def __lt__(self, other: typing.Union[int, CountInterval]):
        return self.before(other)

    def __gt__(self, other: typing.Union[int, CountInterval]):
        return self.after(other)

    def meets(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return other - self.stop == 1  # next in iteration
        return self.stop == other.start

    def meets_inv(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.start - other == 1  # previous in iteration
        return self.start == other.stop

    def overlaps(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            # ?? False for now (simplest boolean semantics)
            return  False # TODO : what ? fallback on another relation ? which one ?
        return self.start < other.start < self.stop < other.stop

    def overlaps_inv(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            # ?? False for now (simplest boolean semantics)
            return  False # TODO : what ? fallback on another relation ? which one ?
        return other.start < self.start < other.stop < self.stop

    def starts(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self == other # fallback on equality
        return self.start == other.start and self.stop < other.stop

    def starts_inv(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.start == other  # lower bound equality sufficient
        return self.start == other.start and self.stop > other.stop

    def during(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return False  # not possible ?? TODO : what about equality ?
        return other.start < self.start and self.stop < other.stop

    def during_inv(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.start < other < self.stop
        return self.start < other.start and other.stop < self.stop

    def __contains__(self, item: CountInterval):
        return self.during_inv(item)

    def finishes(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self == other # fallback on equality
        return self.stop == other.stop and self.start > other.start

    def finishes_inv(self, other:  typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return self.stop == other  # higher bound equality sufficient
        return self.stop == other.stop and self.start < other.start

    # Integer computation => interval computation
    def __add__(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return CountInterval(start=self.start + other, stop=self.stop+other)
        # computed interval must contain all possible solutions (uncertainty semantics) => increased size
        return CountInterval(start=self.start + other.start, stop=self.stop + other.stop)

    def __sub__(self, other: typing.Union[int, CountInterval]):
        if isinstance(other, int):
            return CountInterval(start=self.start - other, stop=self.stop - other)
        # computed interval must contain all possible solutions (uncertainty semantics) => increased size
        return CountInterval(start=self.start - other.stop, stop=self.stop - other.start)



# TODO : conversion to int slices for time.time() based timing

# TODO : there is an equivalent representation with start and duration => how to support it here ?
def countinterval(start: int = None, stop: int=None) -> CountInterval:
    """
    A count slice with a [low..high] semantics
    :param start: start of the interval (lower bound)
    :param stop: end of the interval (upperbound)
    :return:
    """
    # sensible defaults
    if start is None:
        start = datetime.now()
    if stop is None:
        stop = start   # specific semantics of interval as int

    return CountInterval(start=start, stop=stop)


if __name__ == '__main__':

    delta = 3

    val = 42

    t1 = countinterval(val, stop=val + 3)
    t2 = countinterval(val, stop=val + 2)

    assert not t2 in t1
    assert t2.starts(t1)
    assert not t1.finishes(t2)




