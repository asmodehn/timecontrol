import datetime
import inspect
import time
from collections import OrderedDict
from collections.abc import Mapping
from collections import namedtuple
import functools
from dataclasses import dataclass, field

import typing

import dpcontracts

from timecontrol.logs.log import Log, Event

# TODO : different kinds of !structured! log / dataframes, etc.


@dataclass(frozen=True)
class CommandCalled(Event):
    args: typing.Tuple = field(default_factory=tuple)
    kwargs: typing.List = field(default_factory=dict)  # TODO : need a hashable type here !
    # TODO : use resolved "bound" arguments, to avoid duplicates... problem : hashing

    # def __hash__(self):
    #     return hash((super(CommandCalled, self).__hash__(), self.args, frozenset(self.kwargs.items())))


class CallLog(Log):  # TODO :see python trace.Trace
    """
    This is an command-call log, as a wallclock-indexed event log datastore (one command-call is an event).
    It is callable, to store a value with the current (wall)clock.
    It applies to only one pydef / command
    """
    def __init__(self):
        super(CallLog, self).__init__()

    @dpcontracts.types()
    def __call__(
            self, event: CommandCalled   # just to specialise the type here
    ):
        return super(CallLog, self).__call__(event)


def call_logged(log: CallLog = CallLog()):
    def decorator(cmd):
        # TODO : nice and clean wrapper
        def wrapper(*args, **kwargs):
            log(CommandCalled(args=args, kwargs=kwargs.items()))
            return cmd(*args, **kwargs)
        return wrapper
    return decorator


if __name__ == '__main__':
    import random

    log = CallLog()

    @call_logged(log=log)
    def rand(p):
        return random.randint(0, p)

    r42 = rand(42)
    r53 = rand(53)

    for c, r in log.items():
        print(f" - {c} => {r}")
