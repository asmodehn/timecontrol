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

from .log import Log, Event
from result import Result


# TODO : different kinds of !structured! log / dataframes, etc.


@dataclass(frozen=True)
class CommandReturned(Event):
    # we use result here to keep return "in-band". we dont want "out-of-band" exceptions breaking the control flow...
    result: Result = field(default_factory=lambda: Result.Ok(None))

    def __hash__(self):
        return hash((super(CommandReturned, self).__hash__(), self.result))


class ResultLog(Log):  # TODO :see python trace.Trace
    """
    This is an command-return log, as a wallclock-indexed event log datastore (one command-return is an event).
    It is callable, to store a value with the current (wall)clock.
    It applies to only one pydef / command
    """

    def __init__(self, timer=datetime.datetime.now):
        super(ResultLog, self).__init__(timer=timer)

    @dpcontracts.types()
    def __call__(
            self, event: CommandReturned  # just to specialise the type here
    ):
        return super(ResultLog, self).__call__(event)


if __name__ == '__main__':
    raise NotImplementedError("TODO : basic example")

