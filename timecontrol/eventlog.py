import datetime
import time
from collections.abc import Mapping

import functools


# TODO : different kinds of !structured! log.


class EventLog(Mapping):  # TODO :see python trace.Trace
    def __init__(self, timer=datetime.datetime.now):
        self.timer = timer
        self.map = {}

    def __call__(
        self, traced_value
    ):  # TODO : enrich this... but python provides only a single return value (even if tuple...)
        # if already called for this time, store a sequence (linearizability !)
        self.map[self.timer()] = self.map.get(self.timer(), []) + [traced_value]
        return traced_value

    def __getitem__(self, item):
        if item > self.timer():
            return KeyError
        else:
            return self.map.get(item, [])

    def __iter__(self):
        return self.map.__iter__()

    async def __aiter__(self):
        # TODO : wait a bit and return when time has elapsed.
        pass

    def __len__(self):
        return self.map.__len__()


def log(fun):

    tr = EventLog()

    def wrapper(*args, **kwargs):

        return tr(fun(*args, **kwargs))

    wrapper._trace = tr  # adding trace

    return wrapper


if __name__ == "__main__":
    import random

    # TODO : different API to make the "action with side effect" nature explicit ?
    @log
    def fun(mx):
        return random.randint(0, mx)

    r = fun(2)
    print(r)

    r = fun(42)
    print(r)

    for e in fun._trace:
        print(e)
