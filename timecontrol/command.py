# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
import datetime
import random
import time
from collections.abc import Mapping
import wrapt

from timecontrol.underlimiter import UnderTimeLimit
from timecontrol.eventlog import EventLog

# WITH decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)


class CommandRunner(Mapping):
    """
    A command, with always the same arguments.
    What changes is the time that flows under our feet...

    So it is a (pure) function of time.
    """

    def __init__(self, impl, args, kwargs, timer = datetime.datetime.now, sleeper=None):
        self.log = EventLog(timer=timer)
        self.impl = impl

        # This is here only to allow dependency injection for testing
        self.sleeper = sleeper
        if self.sleeper is None:
            self.sleeper = asyncio.sleep if asyncio.iscoroutinefunction(impl) else time.sleep

        # Note : instance is supposed to be in args, when decorating instance methods...
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        while True:
            try:
                #  We cannot assume idempotent like for a function. call in all cases.
                res = self.log(self.impl(*self.args, **self.kwargs))
                return res
            except UnderTimeLimit as utl:
                # call is forbidden now. we have no choice but wait.
                # We will never know what would have been the result now.
                self.sleeper(utl.expected - utl.elapsed)

    def __getitem__(self, item):
        return self.log.__getitem__(item)

    def __iter__(self):
        return self.log.__iter__()

    def __len__(self):
        return self.log.__len__()

    # TODO : add memory limit ??
    # TODO:maybe another project : memorycontrol


class Command:

    def __init__(self, timer=datetime.datetime.now, sleeper=None):
        self.timer = timer
        self.sleeper = sleeper

    def __call__(self, impl):

        def lazyrun(*args, **kwargs):
            # Note we do need a function here to grab instance as the first argument.
            # It seems that if we use a class directly, the instance is lost when called,
            # replaced by the class instance being created.

            return CommandRunner(impl, args, kwargs, timer=self.timer, sleeper=self.sleeper)

        return lazyrun
        



# TODO : a command can be observed, and "supposed" a function, to integrate in current system (simulation).
#   This is doable until proven otherwise. Then better model need to be constructed.



if __name__ == '__main__':

    @command
    def rand(p):
        return random.randint(0, p)

    print(rand(6)())

    print(rand(42)())
    print(rand(42)())

