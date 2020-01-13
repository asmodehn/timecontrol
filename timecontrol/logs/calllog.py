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

# TODO : different kinds of !structured! log / dataframes, etc.


@dataclass(frozen=True)
class CommandCalled(Event):
    args: typing.Tuple = field(default_factory=tuple)
    kwargs: typing.Dict = field(default_factory=dict)
    # TODO : use resolved "bound" arguments, to avoid duplicates... problem : hashing

    def __hash__(self):
        return hash((super(CommandCalled, self).__hash__(), self.args, frozenset(self.kwargs.items())))


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


if __name__ == '__main__':
    raise NotImplementedError("TODO : basic example")
