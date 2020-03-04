from __future__ import annotations
from datetime import datetime, timedelta, MAXYEAR, MINYEAR
from enum import Enum

import typing

week = timedelta(weeks=1)
day = timedelta(days=1)
hour = timedelta(hours=1)
minute = timedelta(minutes=1)
second = timedelta(seconds=1)
millisecond = timedelta(milliseconds=1)
microsecond = timedelta(microseconds=1)


class TimeSlice:
    """
    A time span is a timedelta, associated with a timedate. A precision is also needed to get s well behaved directed container.
    Note we use the same structure as a slice... this should come in handy with datetime-based timeseries.
    """

    start: datetime
    stop: datetime
    step: timedelta

    @property
    def median(self) -> datetime:
        return self.start + (self.stop - self.start) / 2

    def __init__(self, start: datetime = None, stop: datetime = None, step: timedelta = None):
        self.start = start
        self.stop = stop
        self.step = step

    def __repr__(self):
        return f"{repr(self.start)}..{repr(self.stop)}"

    def __str__(self):
        return f"{str(self.start)}..{str(self.stop)}"

    # Allen's Interval Algebra: https://en.wikipedia.org/wiki/Allen%27s_interval_algebra
    def __eq__(self, other: TimeSlice):
        return self.start == other.start and  self.stop ==  self.stop and self.step == other.step

    # TODO : some clever function to add interval algebra to slices in general ?
    def after(self, other: TimeSlice):
        return self.start > other.stop

    def before(self, other: TimeSlice):
        return self.stop < other.start

    def __lt__(self, other: TimeSlice):
        return self.before(other)

    def __gt__(self, other: TimeSlice):
        return self.after(other)

    def meets(self, other: TimeSlice):
        return self.stop == other.start

    def meets_inv(self, other: TimeSlice):
        return self.start == other.stop

    def overlaps(self, other: TimeSlice):
        return self.start < other.start < self.stop < other.stop

    def overlaps_inv(self, other: TimeSlice):
        return other.start < self.start < other.stop < self.stop

    def starts(self, other: TimeSlice):
        return self.start == other.start and self.stop < other.stop

    def starts_inv(self, other: TimeSlice):
        return self.start == other.start and self.stop > other.stop

    def during(self, other: TimeSlice):
        return other.start < self.start and self.stop < other.stop

    def during_inv(self, other: TimeSlice):
        return self.start < other.start and other.stop < self.stop

    def __contains__(self, item: TimeSlice):
        return self.during_inv(item)

    def finishes(self, other: TimeSlice):
        return self.stop == other.stop and self.start > other.start

    def finishes_inv(self, other: TimeSlice):
        return self.stop == other.stop and self.start < other.start

    # We can iterate on periodic timeintervals only
    def __iter__(self):
        return self

    def __next__(self):  # TODO : implement periodic time interval...
        try:
            return TimeSlice(start= self.start + self.step, stop=self.stop + self.step, step= self.step)
        except Exception as e:
            print(e)  # TODO : find exception
            raise StopIteration


# TODO : conversion to int slices for time.time() based timing


def timeslice(start: datetime = None, stop=None, step=None) -> TimeSlice:
    """
    A time slice with a [now..future] bias on creation
    :param start:
    :param stop:
    :param step:
    :return:
    """
    # sensible defaults
    if step is None:
        step = timedelta()
    if start is None:
        start = datetime.now()
    if stop is None:
        if step >= timedelta():
            stop = datetime(year=MAXYEAR, month=12, day=31)
        else:  # backwards
            stop = datetime(year=MINYEAR, month=1, day=1)

    return TimeSlice(start=start, stop=stop, step=step)


if __name__ == '__main__':

    delta = week * 3

    now = datetime.now()

    t1 = timeslice(now, stop=now + timedelta(days= 3))
    t2 = timeslice(now, stop=now + timedelta(days= 2))

    assert not t2 in t1
    assert t2.starts(t1)
    assert not t1.finishes(t2)


