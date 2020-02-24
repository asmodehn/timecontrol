# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import time
import inspect
from collections.abc import Mapping

import typing
from result import Result

from timecontrol.eventful import (
    EventfulDef, CommandCalled, CommandReturned, CommandReturnedLate, eventful, TimePeriod,
    TimePoint,
)


# WITH decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)
# TODO : rethink... maybe not ? @funclass @cmdclass @agentclass, etc.


@dataclass(frozen=True, init=False)
class CommandRun(CommandReturned):
    # Note : Here the event semantic is hte result : the important time is when result was received.
    call: typing.Optional[CommandCalled]
    # call is optional because we might not have observed it/logged the even for it...
    # In controlled environment, we focus our expectations on the result, making the call optional
    # Note

    def __init__(self, call: CommandCalled, result: Result, timestamp: typing.Union[int, datetime] = None):
        object.__setattr__(self, "call", call)
        super(CommandRun, self).__init__(result=result, timestamp=timestamp)

    @property
    def args(self):
        return self.call.args

    @property
    def kwargs(self):
        return self.call.kwargs


class Command:
    """
    Eidos extension in the special case of command (at most one back for one call)

    """

    def __init__(self, cmd: EventfulDef, memory: OrderedDict=None):

        # TODO : be able to extend this, by writing to external system (file/db/etc.)...
        self.memory = OrderedDict() if memory is None else memory
        self.cmd = cmd

    def __call__(
            self, *args, **kwargs
    ):

        gen = self.cmd(*args, **kwargs)

        # using send() here to be similar to async usecase
        call_evt = gen.send(None)
        res_evt = gen.send(None)

        self.memory.setdefault(res_evt.timestamp, set())
        self.memory[res_evt.timestamp].add(CommandRun(
            call=call_evt, result=res_evt.result, timestamp=res_evt.timestamp
        ))

        # recovering usual pydef behavior here
        if res_evt.result:
            return res_evt.result.value
        else:
            raise res_evt.result.value


class ASyncCommand(Command):

    async def __call__(self, *args, **kwargs):

        gen = self.cmd(*args, **kwargs)

        # since we know there should only be two
        call_evt = await gen.asend(None)
        res_evt = await gen.asend(None)

        self.memory.setdefault(res_evt.timestamp, set())
        self.memory[res_evt.timestamp].add(CommandRun(
            call=call_evt, result=res_evt.result, timestamp=res_evt.timestamp
        ))

        # closing generator explicitely to keep control
        await gen.aclose()

        # recovering usual pydef behavior here
        if res_evt.result:
            return res_evt.result.value
        else:
            raise res_evt.result.value


def command(
        ratelimit: typing.Optional[TimePeriod] = None,
        timer: typing.Callable[[], TimePoint] = datetime.now,
        sleeper: typing.Callable[[TimePeriod], None]=None
):

    # Note : timeframe doesnt make sense for a command.
    with_events = eventful(ratelimit=ratelimit, timer=timer, sleeper=sleeper)

    def decorator(cmd):
        if inspect.iscoroutinefunction(cmd):
            return ASyncCommand(with_events(cmd))
        else:
            return Command(with_events(cmd))

    return decorator

# class CommandRunner(Mapping):
#     """
#     A command, with always the same arguments.
#
#     This is an async interface as it is "more generic" than usual sync one.
#     It also allows "executing in the background" from the user point of view, if so desired...
#
#     Note : in here we always have a 1:1 match request-response, and an ASAP time semantics (with underlimit as exception)
#
#     """
#
#     def __init__(self, impl, args, kwargs, timer=datetime.now, sleeper=None):
#         sleeper = asyncio.sleep if sleeper is None else sleeper
#         self.log = CommandLog()
#         self._impl = command_logged(log=self.log, timer=timer)(impl)  # branching logging early.
#
#         # This is here only to allow dependency injection for testing
#         self._sleeper = sleeper
#
#         # Note : instance is supposed to be in args, when decorating instance methods...
#         self._args = args
#         self._kwargs = kwargs
#
#         # In the AsyncRunner case, we need to open the loop (to allow sync or async usages)
#         self._timer = timer
#         self._sleeping = timedelta()  # is set to True when we are sleeping
#         self._sleepstart = self._timer()  # sleeping by default (as in "not running")
#
#     @property
#     def sleeping(self):
#         # when we are sleeping :
#         d: timedelta = self._sleepstart + self._sleeping - self._timer()
#
#         if d < timedelta():
#             return d
#         else:  # not sleeping
#             return 0
#
#     async def __call__(
#         self,
#             # TODO : maybe also integrate space representation here (agent id, etc.)
#     ):
#         """ Call to execute the command.
#         Notes:
#         - An underlimit exception, just means the command was called a bit early,
#           so we wait in flow and recurse to call it.
#         - An overlimit exception means the commnd was not called fast enough.
#           Not handled here -> it is a controle/schedule problem.
#         """
#         #call = CommandCalled(args=self._args, kwargs=[kwa for kwa in self._kwargs.items()])
#         # TODO : log call (partial ?)
#         try:
#             self._sleeping = timedelta(seconds=0)
#             #  We cannot assume idempotent like for a function. call in all cases.
#             if asyncio.iscoroutinefunction(self._impl):
#                 response = await self._impl(*self._args, **self._kwargs)
#             else:  # also handling the synchronous case, synchronously.
#                 response = self._impl(*self._args, **self._kwargs)
#
#             # TODO : convert response into hashable ?
#             #run = CommandRun(call = call, result=response)
#
#             #res = self.log(run)
#             self._last_call = self._timer()  # it has been called !
#             return response  # we need to return the exact response here to keep the usual python call() semantics
#             # #TODO : how do we get CommandRun outside ? => via the log...
#         except UnderTimeLimit as utl:
#             # call is forbidden now. we have no choice but wait.
#             # We will never know what would have been the result now.
#             self._sleeping = timedelta(seconds=utl.expected - utl.elapsed)
#
#             if inspect.iscoroutinefunction(
#                 self._sleeper
#             ):  # because we cannot be sure of our sleeper...
#                 await self._sleeper(self._sleeping.seconds)
#             else:
#                 self._sleeper(self._sleeping.seconds)
#
#             return await self()
#             # Note : we recurse directly here to guarantee ONE call ASAP (usual semantics)
#
#         except Exception as exc:
#             raise  # reraise anything else !
#
#     def __getitem__(self, item):
#         return self.log.__getitem__(item)
#
#     def __iter__(self):
#         return self.log.__iter__()
#
#     def __len__(self):
#         return self.log.__len__()

#
# class Command:
#     def __init__(self, timer=datetime.now, sleeper=None):
#         self.timer = timer
#         self.sleeper = sleeper
#
#     def __call__(self, impl):
#         nest = self
#
#         if inspect.isclass(impl):
#
#             class CmdClassWrapper:
#                 def __init__(self, *args, **kwargs):
#                     self._impl = impl(*args, **kwargs)
#
#                 def __getattr__(self, item):
#                     # forward all unknown attribute to the implementation
#                     return getattr(self._impl, item)
#
#                 def __call__(self, *args, **kwargs):
#                     # This is our lazyrun
#                     return CommandRunner(
#                         self._impl,
#                         args,
#                         kwargs,
#                         timer=nest.timer,
#                         sleeper=nest.sleeper,
#                     )
#
#             return CmdClassWrapper
#
#         else:  # function or instance method (bound or unbound, lazyrun will pass the instance as first argument
#
#             def lazyrun(*args, **kwargs):
#                 # Note: we do need a function here to grab instance as the first argument.
#                 # It seems that if we use a class directly, the instance is lost when called,
#                 # replaced by the class instance being created.
#                 return CommandRunner(
#                     impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper
#                 )
#
#             return lazyrun


# TODO : a command can be observed, and "supposed" a function, to integrate in current system (simulation).
#   This is doable until proven otherwise. Then better model need to be constructed.


if __name__ == "__main__":

    # # SYNC
    @command()
    def rand(p):
        return random.randint(0, p)

    r42 = rand(42)
    # Ths will loop until you kill the program
    # because it is synchronous code
    print(r42)

    for ts, evt in rand.memory.items():
        print(f"{ts}: {evt}")

    # # ASYNC
    @command()
    async def arand(p):
        await asyncio.sleep(1)
        res = random.randint(0, p)
        print(res)  # for immediate print
        return res

    r6 = arand(6)
    r42 = arand(42)

    asyncio.run(r6)

    asyncio.run(r42)

    for ts, evt in arand.memory.items():
        print(f"{ts}: {evt}")

