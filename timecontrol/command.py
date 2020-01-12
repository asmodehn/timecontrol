# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
import datetime
import random
import time
import inspect
from collections.abc import Mapping

from timecontrol.overlimiter import OverTimeLimit
from timecontrol.underlimiter import UnderTimeLimit
from timecontrol.eventlog import EventLog

# WITH decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)


class CommandRunner(Mapping):
    """
    A command, with always the same arguments.
    What changes is the time that flows under our feet...
    So it is a (pure) function of time, provided good enough time resolution.

    Note : this is here for illustration and tests purposes.
    Since it starts an infinite loop it is not really usable. You probably want CommandASyncRunner.
    """

    def __init__(self, impl, args, kwargs, timer=datetime.datetime.now, sleeper=None):
        sleeper = time.sleep if sleeper is None else sleeper
        self.log = EventLog(timer=timer)
        self._impl = impl

        # This is here only to allow dependency injection for testing
        self._sleeper = sleeper

        # Note : instance is supposed to be in args, when decorating instance methods...
        self._args = args
        self._kwargs = kwargs

    def __call__(self, cps):
        delay = 0  # initial is "asap" usual semantics
        while True:
            try:
                self._sleeper(delay)
                #  We cannot assume idempotent like for a function. call in all cases.
                res = self.log(self._impl(*self._args, **self._kwargs))
                cps(res)
            except UnderTimeLimit as utl:
                # call is forbidden now. we have no choice but delay the call.
                # We will never know what would have been the result now.
                delay = utl.expected - utl.elapsed  # calling with the "leftover" delay since underlimiter prevented call this time

            except OverTimeLimit as otl:
                # call came too late this time ! make it happen faster next time...
                delay=otl.expected - (otl.elapsed - otl.expected)  # call with reduced delay

    def __getitem__(self, item):
        return self.log.__getitem__(item)

    def __iter__(self):
        return self.log.__iter__()

    def __len__(self):
        return self.log.__len__()

    # TODO : add log memory limit ??


class CommandASyncRunner(CommandRunner):
    """
    A command, with always the same arguments.

    This is an async interface for the command runner.
    It allows "looping in the background" from the user point of view...

    """

    def __init__(self, impl, args, kwargs, timer=datetime.datetime.now, sleeper=None):
        sleeper = asyncio.sleep if sleeper is None else sleeper
        super(CommandASyncRunner, self).__init__(
            impl=impl, args=args, kwargs=kwargs, timer=timer, sleeper=sleeper
        )

    async def __call__(
        self, cps, delay=0  # cps as continuation passing...
    ):  # we override the synchronous call with an asynchronous one
        try:
            if inspect.iscoroutinefunction(
                self._sleeper
            ):  # because we cannot be sure of our sleeper...
                await self._sleeper(delay)
            else:
                self._sleeper(delay)

            #  We cannot assume idempotent like for a function. call in all cases.

            if asyncio.iscoroutinefunction(self._impl):
                res = self.log(await self._impl(*self._args, **self._kwargs))
            else:  # also handling the synchronous case, synchronously.
                res = self.log(self._impl(*self._args, **self._kwargs))
            cps(res)
        except UnderTimeLimit as utl:
            # call is forbidden now. we have no choice but wait.
            # We will never know what would have been the result now.
            self(cps = cps, delay = utl.expected - utl.elapsed)
            # Note : we recurse here to guarantee ONE call ASAP (usual semantics)
        except OverTimeLimit as otl:
            # call came too late this time ! make it happen faster next time...
            asyncio.create_task(self(cps = cps, delay = otl.expected - (otl.elapsed - otl.expected)))  # call with reduced delay
            # Note : we schedule a new task here to not block the flow (call has been done already)
        else:   # ONLY IF NO exception triggered (happens only once in case of recursion)
            if delay > 0:  # delay == 0 means no recurse (would be sync semantics...). user is expected to trigger call by himself.
                # schedule next pass
                asyncio.create_task(self(cps = cps, delay = delay))

        # Notable Behavior of this design:
        # - at least ONE actual call is guaranteed to happen (immediately, or recursively) and be logged.
        # - loop for *next periodic call* will be scheduled as a task, one time only,
        #   so one await call will terminate as expected (but "loop in background"...).


class Command:
    def __init__(self, timer=datetime.datetime.now, sleeper=None):
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
                    return CommandASyncRunner(
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
                return CommandASyncRunner(
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
        return random.randint(0, p)

    r6 = arand(6)
    r42 = arand(42)

    asyncio.get_event_loop().create_task(r6(cps=print))

    asyncio.get_event_loop().create_task(r42(cps=print))

    asyncio.get_event_loop().run_forever()
