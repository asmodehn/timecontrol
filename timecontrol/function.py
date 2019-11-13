# function implementation as idiomatic python : a dictionnary...
# Mathematical proper "function" is enforced by construction.
# This should lead to a large set of benefits if done properly...

# Note : This is equivalent to functools.lru_cache, with a different api and various options when going oversize...
import asyncio
import time
import typing
from collections.abc import Mapping

from timecontrol.underlimiter import UnderTimeLimit


class Function(Mapping):
    """
    Actually a (pure) Function of one argument. Implemented as a mapping, which it is anyway.
    """
    def __init__(self, impl: typing.Callable, sleeper=None):  # should be a lambda, or something without side effects.
        self.map = {}  # Note : this map is not a trace, and we do NOT need a trace here (function independent of time)
        self.sleeper = sleeper
        if self.sleeper is None:
            self.sleeper = asyncio.sleep if asyncio.iscoroutinefunction(impl) else time.sleep
        self.impl = impl

    # Note : we do NOT want this to be callable,
    #        to make it explicit this is not an action/process, but a (abstract - lazy) structure.

    def __getitem__(self, item):
        try:
            # TODO : maybe use lru cache instead, but find how to provide direct access to the cache...
            # and hook the timer when actually executing...
            # OR assume the cache retrieval is always fast enough ??????
            return self.map[item]
        except KeyError as ke:
            while item not in self.map:
                try:
                    self.map[item] = self.impl(item)
                    # TODO : trace calls (internal, relative time, since program start. debugging / profiling purposes)
                except UnderTimeLimit as utl:
                    # This is a pure function, time doesnt matter -> we can sleep a bit.  #TODO : But why do we have an undertimelimit then ??
                    self.sleeper(utl.expected - utl.elapsed)
                    # TODO : maybe we should use hte opportunity to bypass this and verify things (will take more time, but might be useful to enforce purity...)

            return self.map[item]

    def __iter__(self):
        return self.map.__iter__()

    def __len__(self):
        return self.map.__len__()

    # TODO : add memory limit ??
    # TODO: probably another project : memorycontrol

# NO decorator to encourage consistent coding style :
#   function as lambdas in Function objects (coroutines and procedures still supported)
#   commands as decorated python procedures (coroutines and lambda still supported)

# TODO: goal here is to simplify things by marking part of your program functional
#   => In that case many tooling (trace, profiling and stuff will be disabled by default)


if __name__ == '__main__':

    f = Function(impl=lambda x: x + 4)

    print(f[6])

    print(f[42])
    print(f[42])

