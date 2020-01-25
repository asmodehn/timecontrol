# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
from datetime import datetime, timedelta
import random
import time
import inspect
from collections.abc import Mapping

from timecontrol.logs.commandlog import CommandLog, CommandReturned, CommandRun, command_logged
from timecontrol.logs.calllog import CommandCalled
from timecontrol.underlimiter import UnderTimeLimit

# WITH decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)
# TODO : rethink... maybe not ? @funclass @cmdclass @agentclass, etc.


class CommandRunner(Mapping):
    """
    A command, with always the same arguments.

    This is an async interface as it is "more generic" than usual sync one.
    It also allows "executing in the background" from the user point of view, if so desired...

    Note : in here we always have a 1:1 match request-response, and an ASAP time semantics (with underlimit as exception)

    """

    def __init__(self, impl, args, kwargs, timer=datetime.now, sleeper=None):
        sleeper = asyncio.sleep if sleeper is None else sleeper
        self.log = CommandLog()
        self._impl = command_logged(self.log)(impl)  # branching logging early.

        # This is here only to allow dependency injection for testing
        self._sleeper = sleeper

        # Note : instance is supposed to be in args, when decorating instance methods...
        self._args = args
        self._kwargs = kwargs

        # In the AsyncRunner case, we need to open the loop (to allow sync or async usages)
        self._timer = timer
        self._sleeping = timedelta()  # is set to True when we are sleeping
        self._sleepstart = self._timer()  # sleeping by default (as in "not running")

    @property
    def sleeping(self):
        # when we are sleeping :
        d: timedelta = self._sleepstart + self._sleeping - self._timer()

        if d < timedelta():
            return d
        else:  # not sleeping
            return 0

    async def __call__(
        self,
            # TODO : maybe also integrate space representation here (agent id, etc.)
    ):
        """ Call to execute the command.
        Notes:
        - An underlimit exception, just means the command was called a bit early,
          so we wait in flow and recurse to call it.
        - An overlimit exception means the commnd was not called fast enough.
          Not handled here -> it is a controle/schedule problem.
        """
        #call = CommandCalled(args=self._args, kwargs=[kwa for kwa in self._kwargs.items()])
        # TODO : log call (partial ?)
        try:
            self._sleeping = timedelta(seconds=0)
            #  We cannot assume idempotent like for a function. call in all cases.
            if asyncio.iscoroutinefunction(self._impl):
                response = await self._impl(*self._args, **self._kwargs)
            else:  # also handling the synchronous case, synchronously.
                response = self._impl(*self._args, **self._kwargs)

            # TODO : convert response into hashable ?
            #run = CommandRun(call = call, result=response)

            #res = self.log(run)
            self._last_call = self._timer()  # it has been called !
            return response  # we need to return the exact response here to keep the usual python call() semantics
            # #TODO : how do we get CommandRun outside ? => via the log...
        except UnderTimeLimit as utl:
            # call is forbidden now. we have no choice but wait.
            # We will never know what would have been the result now.
            self._sleeping = timedelta(seconds=utl.expected - utl.elapsed)

            if inspect.iscoroutinefunction(
                self._sleeper
            ):  # because we cannot be sure of our sleeper...
                await self._sleeper(self._sleeping.seconds)
            else:
                self._sleeper(self._sleeping.seconds)

            return await self()
            # Note : we recurse directly here to guarantee ONE call ASAP (usual semantics)

        except Exception as exc:
            raise  # reraise anything else !

    def __getitem__(self, item):
        return self.log.__getitem__(item)

    def __iter__(self):
        return self.log.__iter__()

    def __len__(self):
        return self.log.__len__()


class Command:
    def __init__(self, timer=datetime.now, sleeper=None):
        self.timer = timer
        self.sleeper = sleeper

    def __call__(self, impl):
        nest = self

        if inspect.isclass(impl):

            class CmdClassWrapper:
                def __init__(self, *args, **kwargs):
                    self._impl = impl(*args, **kwargs)

                def __getattr__(self, item):
                    # forward all unknown attribute to the implementation
                    return getattr(self._impl, item)

                def __call__(self, *args, **kwargs):
                    # This is our lazyrun
                    return CommandRunner(
                        self._impl,
                        args,
                        kwargs,
                        timer=nest.timer,
                        sleeper=nest.sleeper,
                    )

            return CmdClassWrapper

        else:  # function or instance method (bound or unbound, lazyrun will pass the instance as first argument

            def lazyrun(*args, **kwargs):
                # Note: we do need a function here to grab instance as the first argument.
                # It seems that if we use a class directly, the instance is lost when called,
                # replaced by the class instance being created.
                return CommandRunner(
                    impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper
                )

            return lazyrun


# TODO : a command can be observed, and "supposed" a function, to integrate in current system (simulation).
#   This is doable until proven otherwise. Then better model need to be constructed.


if __name__ == "__main__":

    # # SYNC
    # @Command()
    # def rand(p):
    #     return random.randint(0, p)
    #
    # r42 = rand(42)
    # # Ths will loop until you kill the program
    # # because it is synchronous code
    # r42(cps=print)

    # ASYNC
    @Command()
    async def arand(p):
        res = random.randint(0, p)
        print(res)

    r6 = arand(6)
    r42 = arand(42)

    asyncio.get_event_loop().create_task(r6())

    asyncio.get_event_loop().create_task(r42())

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt as ki:
        for c in r6:
            print(c)
        for c in r42:
            print(c)
        asyncio.get_event_loop().close()
