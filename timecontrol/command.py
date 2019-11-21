# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
import datetime
import random
import time
import inspect
from collections.abc import Mapping


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
    """

    def __init__(self, impl, args, kwargs, timer = datetime.datetime.now, sleeper=None):
        sleeper = time.sleep if sleeper is None else sleeper
        self.log = EventLog(timer=timer)
        self._impl = impl

        # This is here only to allow dependency injection for testing
        self._sleeper = sleeper

        # Note : instance is supposed to be in args, when decorating instance methods...
        self._args = args
        self._kwargs = kwargs

    def __call__(self):
        while True:
            try:
                #  We cannot assume idempotent like for a function. call in all cases.
                res = self.log(self._impl(*self._args, **self._kwargs))
                return res
            except UnderTimeLimit as utl:
                # call is forbidden now. we have no choice but wait.
                # We will never know what would have been the result now.
                self._sleeper(utl.expected - utl.elapsed)

    def __getitem__(self, item):
        return self.log.__getitem__(item)

    def __iter__(self):
        return self.log.__iter__()

    def __len__(self):
        return self.log.__len__()

    # TODO : add memory limit ??
    # TODO:maybe another project : memorycontrol


class CommandASyncRunner(CommandRunner):
    """
    A command, with always the same arguments.

    This is an async specialization of the command runner

    """

    def __init__(self, impl, args, kwargs, timer=datetime.datetime.now, sleeper=None):
        sleeper = asyncio.sleep if sleeper is None else sleeper
        super(CommandASyncRunner, self).__init__(impl=impl, args=args, kwargs=kwargs, timer=timer, sleeper=sleeper)

    async def __call__(self):  # we override the synchronous call with an asynchronous one
        while True:
            try:
                #  We cannot assume idempotent like for a function. call in all cases.
                res = self.log(await self._impl(*self._args, **self._kwargs))
                return res
            except UnderTimeLimit as utl:
                # call is forbidden now. we have no choice but wait.
                # We will never know what would have been the result now.
                await self._sleeper(utl.expected - utl.elapsed)


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
                    if asyncio.iscoroutinefunction(self._impl.__call__):
                        return CommandASyncRunner(self._impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper)
                    else:
                        return CommandRunner(self._impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper)

            return CmdClassWrapper

        else:  # function or instance method (bound or unbound, lazyrun will pass the instance as first argument
            def lazyrun(*args, **kwargs):
                # Note: we do need a function here to grab instance as the first argument.
                # It seems that if we use a class directly, the instance is lost when called,
                # replaced by the class instance being created.
                if asyncio.iscoroutinefunction(impl):
                    return CommandASyncRunner(impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper)
                else:
                    return CommandRunner(impl, args, kwargs, timer=nest.timer, sleeper=nest.sleeper)

            return lazyrun
        



# TODO : a command can be observed, and "supposed" a function, to integrate in current system (simulation).
#   This is doable until proven otherwise. Then better model need to be constructed.



if __name__ == '__main__':

    @Command()
    def rand(p):
        return random.randint(0, p)

    print(rand(6)())

    print(rand(42)())
    print(rand(42)())

