from datetime import datetime, timedelta
from enum import Enum

import typing

week = timedelta(weeks=1)
day = timedelta(days=1)
hour = timedelta(hours=1)
minute = timedelta(minutes=1)
second = timedelta(seconds=1)
millisecond = timedelta(milliseconds=1)
microsecond = timedelta(microseconds=1)


class TimeInterval:
    """
    A time interval is a timedelta, centered on a timedate.
    """

    datetime: datetime
    precision: timedelta
    period: timedelta

    @property
    def inf(self):
        return self.datetime - self.precision/2

    @property
    def sup(self):
        return self.datetime + self.precision/2

    def __init__(self, datetime: datetime, precision: timedelta, period: timedelta = None):
        self.datetime = datetime
        self.precision = precision
        self.period = period

    def __repr__(self):
        return repr(self.datetime) + ' ± ' + repr(self.precision)

    def __str__(self):
        return str(self.datetime) + ' ± ' + str(self.precision)

    # Allen's Interval Algebra: https://en.wikipedia.org/wiki/Allen%27s_interval_algebra
    def __eq__(self, other):
        return self.datetime == other.datetime and self.precision == other.precision

    def after(self, other):
        return self.inf > other.sup

    def before(self, other):
        return self.sup < other.inf

    def __lt__(self, other):
        return self.before(other)

    def __gt__(self, other):
        return self.after(other)

    def meets(self, other):
        return self.sup == other.inf

    def meets_inv(self, other):
        return self.inf == other.sup

    def overlaps(self, other):
        return self.inf < other.inf < self.sup < other.sup

    def overlaps_inv(self, other):
        return other.inf < self.inf < other.sup < self.sup

    def starts(self, other):
        return self.inf == other.inf and self.sup < other.sup

    def starts_inv(self, other):
        return self.inf == other.inf and self.sup > other.sup

    def during(self, other):
        return other.inf < self.inf and self.sup < other.sup

    def during_inv(self, other):
        return self.inf < other.inf and other.sup < self.sup

    def __contains__(self, item):
        return self.during_inv(item)

    def finishes(self, other):
        return self.sup == other.sup and self.inf > other.inf

    def finishes_inv(self, other):
        return self.sup == other.sup and self.inf < other.inf

    # We can iterate on periodic timeintervals only
    def __iter__(self):
        return self

    def __next__(self):  # TODO : implement periodic time interval...
        if self.period:
            return TimeInterval(datetime= self.datetime + self.period, precision=self.precision, period=self.period)
        else:
            raise StopIteration


def timeinterval(begin: datetime = None, duration=None, end=None, period=None) -> TimeInterval:
    # TODO : defaults that make sense
    if begin is None:
        begin =  datetime.now()
    if duration is None:
        duration = microsecond  # This is troublesome because non overlapping intervals can become overlapping... TODO : change minimal unit
    # end and period are not mandatory
    if end is None and period is None:
        return TimeInterval(datetime=begin - duration/2, precision=duration)
    elif period is None:  # end is not None
        return TimeInterval(datetime=(begin + end) / 2, precision=(end-begin))
    elif end is None:  # period is not None
        return TimeInterval(datetime=begin - duration/2, precision=duration, period=period)
    else:  # neither end nor period are None
        return TimeInterval(datetime=(begin + end) / 2, precision=max(duration, end-begin), period=period)


if __name__ == '__main__':

    delta = week * 3

    now = datetime.now()

    t1 = timeinterval(now, precision=day * 3)
    t2 = timeinterval(now, precision=day * 2)

    assert t2 in t1
    assert not t1.starts(t2)
    assert not t1.finishes(t2)


