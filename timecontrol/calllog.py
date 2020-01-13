"""
A complementary structure to eventlog, probabilitically abstracting previous results as a functionnal relationship with arguments
"""
import datetime
import inspect
from collections.abc import Mapping
from collections import OrderedDict


class CallLog(Mapping):
    """
        This is a function abstraction.
        It is callable, to store a value with the current (wall)clock.
        """

    def __init__(self, timer=datetime.datetime.now):
        self.timer = timer
        self.map = OrderedDict()  # storing arguments and call times (assumption that many calls will have same args)
        self._last_index = None

    def __call__(
        self, cmd, args, kwargs  # we have to do - and log - the call ourselves
            # here we are not simply waiting for result
    ):
        sig = inspect.Signature.from_callable(cmd)
        bargs = sig.bind(*args, **kwargs)  # CAREFUL : bound arguments not hashable...
        now = self.timer()
        self.map[now] = self.map.get(now, []) + [bargs]  # Note : should be set, but bargs not hashable

        # finally do the call and return
        return cmd(*bargs.args, **bargs.kwargs)  # TODO : maybe merge calllog and eventlog ? (call is an event...)

    def __getitem__(self, item):  # item is a timestamp
        if item > self.timer():
            return KeyError
        else:
            return self.map.get(item, set())
            # TODO : bounded arg conversion here or somewhere else ??
            # calls = set()
            # for ba, t in self.map:
            #     if t == item:
            #         calls.add(ba)
            # return calls  # return empty set if it was never called

    def __iter__(self):
        return self.map.__iter__()
        # TODO : use an invariant mapproxy (lens/immutable view)
        # res = OrderedDict()
        # for ba, t in self.map.items():
        #     res[t] = res.get(t, set()) | {ba}
        # return iter(sorted(res))
    # or do the opposite : store time directly, reindex via boundargs on request...

    async def __aiter__(self):
        # TODO : wait a bit and return when time has elapsed.
        pass

    def __len__(self):
        return self.map.__len__()


def log(fun):

    tr = CallLog()

    def wrapper(*args, **kwargs):

        return tr(fun, args, kwargs)

    wrapper._trace = tr  # adding trace

    return wrapper


if __name__ == "__main__":
    import random

    # TODO : different API to make the "action with side effect" nature explicit ?
    @log
    def fun(mx):
        return random.randint(0, mx)

    r = fun(2)
    print(r)

    r = fun(42)
    print(r)

    for e, ba in fun._trace.items():
        print(f"called on {e} with {ba}")
