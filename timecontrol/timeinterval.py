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


class TimeInterval:
    """
    A time interval is a couple of timedate (timedelta is deduced).

    We rely on this representation to base everything on interval (for simple yet safe real-world correspondance)
    a time delta is considered an idea, an abstraction. we want to remain imperative / practical
    and keep the code directly related to the real world, python style, for easy maintenance.
    """

    start: datetime
    stop: datetime

    @property
    def delta(self) -> timedelta:
        return self.stop - self.start

    @property
    def median(self) -> datetime:
        return self.start + (self.stop - self.start) / 2

    def __init__(self, start: datetime = None, stop: datetime = None):
        self.start = start
        self.stop = stop

    def __repr__(self):
        return f"{repr(self.start)}..{repr(self.stop)}"

    def __str__(self):
        return f"{str(self.start)}..{str(self.stop)}"

    # Allen's Interval Algebra: https://en.wikipedia.org/wiki/Allen%27s_interval_algebra
    def __eq__(self, other: TimeInterval):
        return self.start == other.start and self.stop == other.stop

    def after(self, other: TimeInterval):
        return self.start > other.stop

    def before(self, other: TimeInterval):
        return self.stop < other.start

    def __lt__(self, other: TimeInterval):
        return self.before(other)

    def __gt__(self, other: TimeInterval):
        return self.after(other)

    def meets(self, other: TimeInterval):
        return self.stop == other.start

    def meets_inv(self, other: TimeInterval):
        return self.start == other.stop

    def overlaps(self, other: TimeInterval):
        return self.start < other.start < self.stop < other.stop

    def overlaps_inv(self, other: TimeInterval):
        return other.start < self.start < other.stop < self.stop

    def starts(self, other: TimeInterval):
        return self.start == other.start and self.stop < other.stop

    def starts_inv(self, other: TimeInterval):
        return self.start == other.start and self.stop > other.stop

    def during(self, other: TimeInterval):
        return other.start < self.start and self.stop < other.stop

    def during_inv(self, other: TimeInterval):
        return self.start < other.start and other.stop < self.stop

    def __contains__(self, item: TimeInterval):
        return self.during_inv(item)

    def finishes(self, other: TimeInterval):
        return self.stop == other.stop and self.start > other.start

    def finishes_inv(self, other: TimeInterval):
        return self.stop == other.stop and self.start < other.start


# TODO : conversion to int slices for time.time() based timing

# TODO : there is an equivalent representation with start and duration => how to support it here ?
def timeinterval(start: datetime = None, stop: datetime=None) -> TimeInterval:
    """
    A time slice with a [now..future] bias on creation
    :param start: start of the interval (lower bound)
    :param stop: end of the interval (upperbound)
    :return:
    """
    # sensible defaults
    if start is None:
        start = datetime.now()
    if stop is None:
        stop = datetime(year=MAXYEAR, month=12, day=31)
        # stop = datetime(year=MINYEAR, month=1, day=1)

    return TimeInterval(start=start, stop=stop)


if __name__ == '__main__':

    delta = week * 3

    now = datetime.now()

    t1 = timeinterval(now, stop=now + timedelta(days= 3))
    t2 = timeinterval(now, stop=now + timedelta(days= 2))

    assert not t2 in t1
    assert t2.starts(t1)
    assert not t1.finishes(t2)




