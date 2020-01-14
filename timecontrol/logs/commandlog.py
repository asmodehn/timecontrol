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
    # Note : Here the event semantic is hte result : the important time is when result was received.
    call: typing.Optional[CommandCalled] = field(default_factory=lambda: None)
    # call is optional because we might not have observed it/logged the even for it...
    # In controlled environment, we focus our expectations on the result, making the call optional
    # Note

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

    @dpcontracts.types()
    def __call__(
            self, event: CommandRun  # just to specialise the type here
    ):
        return super(CommandLog, self).__call__(event)


def command_logged(log: CommandLog = CommandLog()):
    def decorator(cmd):
        # TODO :nice and clean wrapper

        def wrapper(*args, **kwargs):
            # tying together call_logged and result_logged here following python call semantics (1 call :1 result)
            call = CommandCalled(args=args, kwargs=kwargs)
            try:
                res = cmd(*args, **kwargs)
                result = Result.Ok(res)
            except Exception as exc:
                result = Result.Err(exc)
            finally:
                log(CommandRun(call=call, result=result))
                return result

        async def async_wrapper(*args,
                                **kwargs):
            # tying together call_logged and result_logged here following python call semantics (1 call :1 result)
            call = CommandCalled(args=args, kwargs=kwargs)
            try:
                res = await cmd(*args, **kwargs)
                result = Result.Ok(res)
            except Exception as exc:
                result = Result.Err(exc)
            finally:
                log(CommandRun(call=call, result=result))
                return result

        if inspect.iscoroutinefunction(cmd):
            return async_wrapper
        else:
            return wrapper

    return decorator


if __name__ == '__main__':

    import random

    log = CommandLog()
    # SYNC
    # @command_logged(log=log)
    # def rand(p):
    #     return random.randint(0, p)
    #
    # r42 = rand(42)
    # r53 = rand(53)

    # for c, r in log.calls.items():
    #     print(f" - {c} => {r}")
    #
    # for c, r in log.results.items():
    #     print(f" - {c} => {r}")
    #
    # for c, r in log.items():
    #     print(f" - {c} => {r}")

    # ASYNC
    import asyncio
    @command_logged(log=log)
    async def rand(p):
        return random.randint(0, p)

    async def scheduler(loop=None):
        import time
        from datetime import timezone
        print(datetime.now(tz=timezone.utc))

        loop = asyncio.get_event_loop() if loop is None else loop

        loop.create_task(rand(42))
        loop.create_task(rand(51))

    asyncio.get_event_loop().run_until_complete(scheduler())

    for c, r in log.items():
        print(f" - {c} => {r}")