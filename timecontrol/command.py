# loose effect implementation as idiomatic python. TODO : refine

# Note : This is meant to be used along with timecontrol.Function to alter a bit python semantics.
# An actual call() means an effect will happen, and the state should be assume different (but the change event was traced)
import asyncio
import datetime
import random
import time
from collections.abc import Mapping

from timecontrol.underlimiter import UnderTimeLimit
from timecontrol.trace import Trace

# WITH decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)


def command(impl, sleeper=None):
    if sleeper is None:
        sleeper = asyncio.sleep if asyncio.iscoroutinefunction(impl) else time.sleep

    class Command(Mapping):
        """
        A command, with always the same arguments.
        What changes is the time that flows under our feet...

        So it is a (pure) function of time.
        """

        def __init__(self, *args, **kwargs):
            self.trace = Trace()
            self.impl = impl
            self.args = args
            self.kwargs = kwargs

        def __call__(self):
            while True:
                try:
                    #  We cannot assume idempotent like for a function. call in all cases.
                    res = self.trace(self.impl(*self.args, **self.kwargs))
                    return res
                except UnderTimeLimit as utl:
                    # call is forbiden now. we have no choice but wait. WE will never know what would have been the result now.
                    sleeper(utl.expected - utl.elapsed)

        def __getitem__(self, item):
            return self.trace.__getitem__(item)

        def __iter__(self):
            return self.trace.__iter__()

        def __len__(self):
            return self.trace.__len__()

        # TODO : add memory limit ??
        # TODO:maybe another project : memorycontrol

    return Command


if __name__ == '__main__':

    @command
    def rand(p):
        return random.randint(0, p)

    print(rand(6)())

    print(rand(42)())
    print(rand(42)())

