import datetime

import typing
from enum import Enum

# Use something from datetime to enforce compatibility somehow
from types import MappingProxyType

from timecontrol.schedules import timeinterval
from timecontrol.schedules.schedule import Intent
from timecontrol.schedules.timeinterval import hour


class timeperiod(Enum):
    """ This represent periodicity (every <*>)"""
    year = 1
    month = 2
    day = 3
    hour = 4
    minute = 5
    second = 6


class ScheduleDict:
    """ A Schedule Dict with some convenience method to navigate the data structure.
    We stick close to core python's datetime semantics.

    Note : for periodic events, it is stored in the event, in charge of rescheduling himself...
    """

    def __init__(self, mapping: typing.Dict[datetime.datetime, typing.Any] = None):
        self._mapping = dict() if mapping is None else mapping
        self.schedule = MappingProxyType(mapping)  # we want to prevent any user modification to the log
        self.timeperiod = timeperiod.year

    # TODO : precision to simplify understanding/manipulation/display
    # @property
    # def minutely(self):
    #
    #     return scheduledict()
    #
    # @property
    # def hourly(self):
    #     return
    #
    # @property
    # def daily(self):
    #     return

    def __call__(self, event):
        # TODO : ensure schedule doesnt have overlapping things... 1 thing at a time ( + tolerance if timecost available )
        return scheduledict({**self.schedule, **{event.timeinterval: event.action}})

    def __getitem__(self, item: typing.Union[datetime.datetime, datetime.date, datetime.time, timeinterval.timeinterval, int]):
        # target, retrieve tasks intersecting
        if isinstance(item, int):
            # return the sub dictionnary of all event happening at that time period (in seconds to match time() unit)
            return ScheduleDict({d: e for d, e in self.schedule
                                 if item in timeinterval.TimeInterval(d.date(), precision=datetime.timedelta(seconds=1))})
        elif isinstance(item, datetime.datetime):
            # return the sub dictionnary of all events happening at that time period (in seconds by default)
            return ScheduleDict({d: e for d, e in self.schedule
                                 if item in timeinterval.TimeInterval(d.date(), precision=datetime.timedelta(seconds=1))})
        # return everything inside a period
        elif isinstance(item, datetime.date):
            return ScheduleDict({d: e for d, e in self.schedule if d.date() == item})
        elif isinstance(item, datetime.time):
            return ScheduleDict({d: e for d, e in self.schedule if d.time() == item})
        elif isinstance(item, timeinterval.TimeInterval):
            return ScheduleDict({d: e for d, e in self.schedule if d in item})

    def __next__(self):
        pass # TODO : take next occuring event.

EmptyScheduleDict = ScheduleDict()


def scheduledict(interval_dict: typing.Dict[timeinterval, Intent]):
    if not interval_dict:
        return EmptyScheduleDict
    else:
        return ScheduleDict(interval_dict)


if __name__ == '__main__':

    sd = ScheduleDict()

    scheduled = sd({timeinterval(begin=datetime.datetime.now(), end=hour*2): 42})

    now = datetime.datetime.now()
    dd[now + timedelta(seconds=4)] = 42

    dd.yearly(42)
    dd.hourly(51)

    dd.month[3] = # absolute (interval)

    assert dd[now] == set()
    assert dd[now.date()] == {(now, 42)}
