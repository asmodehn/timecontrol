from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import Mapping

import typing

import dpcontracts


# Note : Event must be hashable to be storable in a set.
@dataclass(frozen=True)
class Event:
    # todo : support more time representations...
    timestamp: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    # def __hash__(self):  # make sure the event is hashable (storable in a set)
    #     return hash(self.timestamp)


class Log(Mapping):
    """
       This is a generic log, as a wallclock-indexed event datastore (immutable observed event can be almost anything).
       It is callable, to store a value with the current (wall)clock.
       """

    def __init__(self):
        self.map = OrderedDict()

    @property
    def last(self):
        last_timestep = list(self.map.keys())[-1]
        return next(iter(self.map[last_timestep]))  # just pick one element... (expected indeterminism !)
        # we take the last in the list (we might have multiple results in same timestep)
        # TODO : maybe we should implement some kind of tunable probabilistic distribution here...

    @dpcontracts.types()
    def __call__(
            self, event: Event
    ):
        # if already called for this time, store a set (undeterminism)
        # TODO : not duplicate timestamp here...
        self.map[event.timestamp] = self.map.get(event.timestamp, list()) + [event]
        # TODO : SET is better here(but require hashable). List doesn't...
        return event  # identity from the caller point of view. pure side-effecty.

        # TODO : be more than just writing to external system (file/db/etc.)...
        #  Need to "plug into" set of events, in order to have them extracted (customizable) to somewhere else...

    # TODO : maybe just delegate to OrderedDict ? BETTER : mappingproxy ! -> immutable
    def __getitem__(self, timestamp):
        return self.map.get(timestamp, set())

    def __iter__(self):
        return self.map.__iter__()

    def __len__(self):
        return self.map.__len__()

    def __add__(self, other):
        # TODO : add mergeable functionality
        raise NotImplementedError


def logged(log: Log):
    def decorator(cmd):
        # TODO : nice and clean wrapper
        def wrapper(*args, **kwargs):
            log(Event())
            return cmd(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == "__main__":
    import random

    l = Log()

    e1 = Event()

    e2 = Event()

    l(e1)

    l(e2)

    for e in l:
        print(e)
