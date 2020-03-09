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


class DateTimeInterval:
    """
    A time interval is a couple of timedate (timedelta is deduced).

    We rely on this representation to base everything on interval (for simple yet safe real-world correspondance)
    a time delta is considered an idea, an abstraction. we want to remain imperative / practical
    and keep the code directly related to the real world, python style, for easy maintenance.
    """

    # Note : critical semantic difference between countinterval and timeinterval.
    # For count, since it can only increase, the start is the locally certain count.
    #  and stop is the uncertain possible max count. it will converge somewhere inside itself.
    # For time, since it can only increase, but we can only rely our local clock, start is the past timestamp declared,
    #  and stop is the locally measured (certain max) of the event.
    start: datetime
    stop: datetime

    @property
    def delta(self) -> timedelta:
        return self.stop - self.start

    @property
    def median(self) -> datetime:
        return self.start + (self.stop - self.start) / 2

    def __init__(self, start: datetime = None, stop: datetime = None):
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
    def __eq__(self, other: typing.Union[datetime,DateTimeInterval]):
        if isinstance(other, datetime):
            return self.start == self.stop == other
        return self.start == other.start and self.stop == other.stop

    def __hash__(self):
        return hash((self.start, self.stop))

    def after(self, other: typing.Union[datetime,DateTimeInterval]):
        if isinstance(other, datetime):
            return self.start > other
        return self.start > other.stop

    def before(self, other: typing.Union[datetime,DateTimeInterval]):
        if isinstance(other, datetime):
            return self.stop < other
        return self.stop < other.start

    def __lt__(self, other: DateTimeInterval):
        return self.before(other)

    def __gt__(self, other: DateTimeInterval):
        return self.after(other)

    def meets(self, other: typing.Union[datetime,DateTimeInterval]):
        if isinstance(other, datetime):
            return other == self.stop
        return self.stop == other.start

    def meets_inv(self, other: typing.Union[datetime,DateTimeInterval]):
        if isinstance(other, datetime):
            return self.start == other
        return self.start == other.stop

    def overlaps(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            # ?? False for now (simplest boolean semantics)
            return  False # TODO : what ? fallback on another relation ? which one ?
        return self.start < other.start < self.stop < other.stop

    def overlaps_inv(self, other:  typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            # ?? False for now (simplest boolean semantics)
            return  False # TODO : what ? fallback on another relation ? which one ?
        return other.start < self.start < other.stop < self.stop

    def starts(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return self == other # fallback on equality
        return self.start == other.start and self.stop < other.stop

    def starts_inv(self, other:  typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return self.start == other  # lower bound equality sufficient
        return self.start == other.start and self.stop > other.stop

    def during(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return False  # not possible ?? TODO : what about equality ?
        return other.start < self.start and self.stop < other.stop

    def during_inv(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return self.start < other < self.stop
        return self.start < other.start and other.stop < self.stop

    def __contains__(self, item: typing.Union[datetime, DateTimeInterval]):
        return self.during_inv(item)

    def finishes(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return self == other  # fallback on equality
        return self.stop == other.stop and self.start > other.start

    def finishes_inv(self, other: typing.Union[datetime, DateTimeInterval]):
        if isinstance(other, datetime):
            return self.stop == other  # higher bound equality sufficient
        return self.stop == other.stop and self.start < other.start


# TODO : conversion to int slices for time.time() based timing

# TODO : there is an equivalent representation with start and duration => how to support it here ?
def datetimeinterval(start: datetime = None, stop: datetime=None) -> DateTimeInterval:
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
        stop = start + timedelta(microseconds=1)  # specific semantics of datetime as interval, looking ahead
        # stop = datetime(year=MAXYEAR, month=12, day=31)
        # stop = datetime(year=MINYEAR, month=1, day=1)

    return DateTimeInterval(start=start, stop=stop)


if __name__ == '__main__':

    delta = week * 3

    now = datetime.now()

    t1 = datetimeinterval(now, stop=now + timedelta(days= 3))
    t2 = datetimeinterval(now, stop=now + timedelta(days= 2))

    assert not t2 in t1
    assert t2.starts(t1)
    assert not t1.finishes(t2)




