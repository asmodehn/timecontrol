import inspect
from collections import OrderedDict, namedtuple
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime

import typing

import dpcontracts
from result import Result

from timecontrol.logs.calllog import CommandCalled, CallLog, call_logged
from timecontrol.logs.log import Event, Log
from timecontrol.logs.resultlog import CommandReturned, ResultLog, result_logged

CmdSyncLogData = namedtuple("CmdSyncLog", ["call", "result"])


@dataclass(frozen=True)
class CommandRun(CommandReturned):
    # Note This is hte complementary semantic from log
    # storing calls internaly before registering a run on result...
    call: typing.Optional[CommandCalled] = field(default_factory=lambda: None)
    # call is optional because we might not have observed it/logged the even for it...

    @property
    def args(self):
        return self.call.args

    @property
    def kwargs(self):
        return self.call.kwargs

    def __hash__(self):
        """ maintaining only one level of hashing """  # TODO : cleanup hashing strategy. leave it to frozen dataclass for simplicity ?
        return hash((self.timestamp, self.args, frozenset(self.kwargs.items()), self.result))


class CommandLog(Log):  # TODO :see python trace.Trace
    """
    This is an command-return log, as a wallclock-indexed event log datastore (one command-return is an event).
    It is callable, to store a value with the current (wall)clock.
    It applies to only one pydef / command
    """

    def __init__(self):
        self.calls = CallLog()  # call stack (without matching result)...
        self.results = ResultLog()  # result stack (without matching call)...
        super(CommandLog, self).__init__()

    @dpcontracts.types()
    def __call__(
            self, event: typing.Union[CommandCalled, CommandReturned]  # just to specialise the type here
    ):
        if isinstance(event, CommandCalled):
            self.calls(event)
        elif isinstance(event, CommandReturned):
            self.results(event)
            # Here we associate return with latest call
            latest = self.calls
            # => assumes linearization of calls for ONE command !!!
            # TODO: check semantics of async def (reentrant ?? linearized ??)
            # TODO : Isn't this a 'Process' then ??
            return super(CommandLog, self).__call__(CommandRun(call=self.calls.last, result=event.result))
        else:
            raise NotImplementedError("Unknown Event passed to command log")



def command_logged(log: CommandLog):
    # chaining decorators ( as higher order functions )
    def decorator(cmd):
        return call_logged(log=log)(result_logged(log=log)(cmd))
    return decorator
# => Doesnt bring much... Maybe we should do things hte other way (accepting different type of logs in  call_logged and result_logged)

if __name__ == '__main__':

    import random

    log = CommandLog()

    @command_logged(log=log)
    def rand(p):
        return random.randint(0, p)

    r42 = rand(42)
    r53 = rand(53)

    for c, r in log.calls.items():
        print(f" - {c} => {r}")


    for c, r in log.results.items():
        print(f" - {c} => {r}")


    for c, r in log.items():
        print(f" - {c} => {r}")
