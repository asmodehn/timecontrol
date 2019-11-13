import datetime
from collections.abc import Mapping

import functools

#
# class Tracer(Mapping):
#     """ A class to trace multiple calls to a function/method.
#     This is used along with overlimiter and underlimiter to provide something to potentially cache and return results from.
#     """
#
#     def __init__(self):
#         self.trace = pd.DataFrame(columns = ["args", "return"])
#         self._decorator = None
#
#     def __call__(self, fun):
#         """ as a decorator """
#         if self._decorator:
#             self._decorator
#
#         def wrapper(*args, **kwargs):
#             # TODO :  see functools.lru_cache implementation. What is the link ???
#
#             res = fun(*args, **kwargs)
#
#             self.trace.append({"timestamp": datetime.datetime.now(), "args": args, "return": res}.update({k: v for k, v in kwargs.items()}),
#                               sort=False)
#
#             return res
#
#         self._decorator = wrapper
#
#         return self
#
#     def __getitem__(self, item):
#         return self.trace.get(item, None)
#
#     def __iter__(self):
#         return self.trace.iteritems()
#
#     def __len__(self):
#         return len(self.trace)


# def trace(fun):
#
#     class Tracer(Mapping):
#         """ A class to trace multiple calls to a function/method.
#         This is used along with overlimiter and underlimiter to provide something to potentially cache and return results from.
#         """
#
#         def __init__(self):  # Time idempotent ? Location Idempotent ?
#             self.trace = {}
#
#         def __call__(self, *args, **kwargs):
#             # TODO :  see functools.lru_cache implementation. What is the link ???
#
#             res = fun(*args, **kwargs)
#
#             call_trace = {k: v for k, v in kwargs.items()}
#             call_trace["args"] = args
#             call_trace["return"] = res
#
#             # TODO : different roles depending on time here...
#             # Probably a global absolute time, means persistent (DB) storage...
#             self.trace[datetime.datetime.now()] = call_trace
#
#             return res
#
#         def __getitem__(self, item):
#             return self.trace.get(item, None)
#
#         def __iter__(self):
#             # TODO : pandas ?
#             return self.trace.__iter__()
#
#         def __len__(self):
#             return len(self.trace)
#
#     return Tracer()

class FunTrace:
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
                    # This is a pure function, time doesnt matter -> we can sleep a bit.
                    self.sleeper(utl.expected - utl.elapsed)

            return self.map[item]


class Trace(Mapping):   # TODO :see python trace.Trace

    def __init__(self):
        self.map = {}

    def __call__(self, traced_value):  # TODO : enrich this... but python provides only a single return value (even if tuple...)
        self.map[datetime.datetime.now()] = traced_value
        return traced_value

    def __getitem__(self, item):
        return self.map[item]

    def __iter__(self):
        return self.map.__iter__()

    def __len__(self):
        return self.map.__len__()


def trace(fun):

    tr = Trace()

    def wrapper(*args, **kwargs):

        return tr(fun(*args, **kwargs))

    wrapper._trace = tr  # adding trace

    return wrapper


if __name__ == '__main__':
    import random

    # TODO : different API to make the "action with side effect" nature explicit ?
    @trace
    def fun(mx):
        return random.randint(0, mx)


    r = fun(2)
    print(r)

    r = fun(42)
    print(r)

    for e in fun._trace:
        print(e)


