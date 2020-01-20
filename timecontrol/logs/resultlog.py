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
from result import Result


# TODO : different kinds of !structured! log / dataframes, etc.


@dataclass(frozen=True)
class CommandReturned(Event):
    # we use result here to keep return "in-band". we dont want "out-of-band" exceptions breaking the control flow...
    result: Result = field(default_factory=lambda: Result.Ok(None))

    # def __hash__(self):
    #     return hash((super(CommandReturned, self).__hash__(), self.result))


class ResultLog(Log):  # TODO :see python trace.Trace
    """
    This is an command-return log, as a wallclock-indexed event log datastore (one command-return is an event).
    It is callable, to store a value with the current (wall)clock.
    It applies to only one pydef / command
    """

    def __init__(self):
        super(ResultLog, self).__init__()

    @dpcontracts.types()
    def __call__(
            self, event: CommandReturned  # just to specialise the type here
    ):
        return super(ResultLog, self).__call__(event)


def result_logged(log: ResultLog = ResultLog()):
    def decorator(cmd):
        # TODO :nice and clean wrapper
        def wrapper(*args, **kwargs):
            try:
                res = cmd(*args, **kwargs)
                result = Result.Ok(res)
            except Exception as exc:
                result = Result.Err(exc)
            finally:
                log(CommandReturned(result=result))
                return result
        return wrapper
    return decorator


if __name__ == '__main__':
    import random

    log = ResultLog()
    @result_logged(log=log)
    def rand(p):
        return random.randint(0, p)

    r42 = rand(42)
    r53 = rand(53)

    for c, r in log.items():
        print(f" - {c} => {r}")


