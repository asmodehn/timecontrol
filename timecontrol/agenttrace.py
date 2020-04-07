from __future__ import annotations

import functools
import inspect
from asyncio import Future, Task
from collections.abc import Mapping

import typing
from dataclasses import dataclass
from inspect import BoundArguments

import wrapt

"""
AgentTrace, keeping track of all futures for this agent.
"""


# the simplest implementation of hashable frozendict, waiting for a standard one in python (see PEP 416 for more info)
def frozendict(mydict: dict = None):
    return frozenset([
            # we need to recursively support dict in values
            (e[0], frozendict(e[1])) if isinstance(e[1], dict)
            else e  # otherwise just pass the bound argument directly (tuples are hashable)
            for e in mydict.items()
        ])
# immutable (frozen) => readonly (more than MappingProxyType)
# + Hashable => Like a namedtuple but dynamically assigning keys
# TODO maybe : + directed container / implicit bimonad => collapse all nested dicts to only one level.


class BoundArgumentsHashable:

    def __init__(self, bargs: BoundArguments):
        self.arguments_final= frozendict(bargs.arguments)

    def __hash__(self):
        return hash()





#
#
# @dataclass(frozen=True)
# class CommandReturned(Event):
#     # we use result here to keep return "in-band". we dont want "out-of-band" exceptions breaking the control flow...
#     result: Result = field(default_factory=lambda: Result.Ok(None))
#     result_timestamp: typing.Union[int, datetime] = field(default_factory=lambda: datetime.now(tz=timezone.utc))
#
#     # def __hash__(self):
#     #     return hash((super(CommandReturned, self).__hash__(), self.result))
#
# @dataclass(frozen=True,init=False)
# class CommandRun:
#     # Note : Here the event semantic is hte result : the important time is when result was received.
#     call: typing.Optional[CommandCalled]
#     # call is optional because we might not have observed it/logged the even for it...
#     # In controlled environment, we focus our expectations on the result, making the call optional
#     # Note
#
#     def __init__(self, call: CommandCalled, result: Result, timestamp: typing.Union[int, datetime] = None):
#         object.__setattr__(self, "call", call)
#         super(CommandRun, self).__init__(result=result, timestamp=timestamp)
#
#     @property
#     def args(self):
#         return self.call.args
#
#     @property
#     def kwargs(self):
#         return self.call.kwargs
#     #
#     # def __hash__(self):
#     #     """ maintaining only one level of hashing """  # TODO : cleanup hashing strategy. leave it to frozen dataclass for simplicity ?
#     #     return hash((self.timestamp, self.args, frozenset(self.kwargs.items()), self.result))


# Note : This could also be viewed as a log of Futures !!
class TracedCallable(wrapt.FunctionWrapper, Mapping):

    def __init__(self, wrapped, wrapper, enabled=None):
        self.funwrapper = decorated_callable
        self.signature = signature
        self.trace = dict()

    """ A class to delegate call to a wrapt decorated synchronous callable"""
    @wrapt.decorator
    def __call__(self, wrapped: typing.Callable[..., _T], instance, args, kwargs) -> _T:
        bound_args = self.signature.bind(*args, **kwargs)
        bound_args.apply_defaults()
        frozenargs = frozendict(bound_args.arguments)
        self.trace[frozenargs] = self.funwrapper(*bound_args.args, **bound_args.kwargs)
        return self.trace[frozenargs]  # getting result from trace to make sure it works.

    # TODO : refining syntax to have same calling convention, just difference being we grab from the trace (memoization)
    def __getitem__(self, item: typing.Union[BoundArguments, typing.Dict[...]]):

        if isinstance(item, BoundArguments):
            item = frozendict(item.arguments)
        else:  # we just attempt to freeze arguments
            item = frozendict(item)

        return self.trace[item]

    def __iter__(self):
        """ Iterator through the past terminated tasks, in reverse order => will eventually terminate """
        done = {k: v if not isinstance(v, Task) else v.result()  # should be done !
                for k, v in reversed(self.trace.items()) if not isinstance(v, Task) or v.done()}

        for k, v in done:
            # if we are yielding the key, we can change the value from a Task to the result
            self.trace[k] = v
            yield k

    async def __aiter__(self):
        """ Iterator towards the future, potentially blocking, skipping already finished items"""
        running = {k: v for k, v in self.trace.items() if isinstance(v, Task) and not v.done()}

        for k, v in running:
            # if we are yielding the key, we can change the value from a Task to the result
            self.trace[k] = await v
            yield k

    def __len__(self):
        return len(self.trace)


class TracedBoundFunctionWrapper(wrapt.BoundFunctionWrapper):

    def __init__(self, descriptor, instance,
                        _self_wrapper, _self_enabled,
                        _self_binding, _self_parent):
        super(TracedBoundFunctionWrapper, self).__init__(descriptor, instance,
                        _self_wrapper, _self_enabled,
                        _self_binding, _self_parent)
        self._self_signature = _self_parent._self_signature
        self._self_trace = _self_parent._self_trace

    def __call__(self, *args, **kwargs):
        instance, args, kwargs, result = super(TracedBoundFunctionWrapper, self).__call__(*args, **kwargs)
        # we bind afterwards to retrieve the instance from wrapt
        bound_args = self._self_signature.bind(instance, *args, **kwargs)
        #  we dont need to apply default here, it has already been done during the call
        frozenargs = frozendict(bound_args.arguments)
        self._self_trace[frozenargs] = result
        return self._self_trace[frozenargs]  # getting result from trace to make sure it's accessible.


class TracedFunctionWrapper(wrapt.FunctionWrapper):

    __bound_function_wrapper__ = TracedBoundFunctionWrapper

    def __init__(self, wrapped, wrapper, signature):
        super(TracedFunctionWrapper, self).__init__(wrapped, wrapper)
        self._self_signature = signature
        self._self_trace = dict()

    def __call__(self, *args, **kwargs):
        instance, args, kwargs, result = super(TracedFunctionWrapper, self).__call__(*args, **kwargs)
        # we bind afterwards to retrieve the instance from wrapt
        if instance is None:   # tentative : TODO : thorough testing
            bound_args = self._self_signature.bind(*args, **kwargs)
        else:
            bound_args = self._self_signature.bind(instance, *args, **kwargs)
        #  we dont need to apply default here, it has already been done during the call
        frozenargs = frozendict(bound_args.arguments)
        self._self_trace[frozenargs] = result
        return self._self_trace[frozenargs]  # getting result from trace to make sure it's accessible.


# TODO : add a pure option declaration (to grab result from trace when possible)
def traced_function_wrapper(wrapper):
    @functools.wraps(wrapper)
    def _wrapper(wrapped):
        return TracedFunctionWrapper(wrapped, wrapper, inspect.signature(wrapped))
    return _wrapper


# TODO : add a pure option declaration (to grab result from trace when possible)
def traced():
    @traced_function_wrapper
    def traced_decorator(wrapped, instance, args, kwargs):
        # Here we return the element we want stored in the trace for this wrapped function/method
        return instance, args, kwargs, wrapped(*args, **kwargs)
        # the functionwrapper will only forward the result
    return traced_decorator


if __name__ == '__main__':

    @traced()
    def myfun(a = 39):
        return a + 3

    assert myfun(48) == 51

    print (myfun._self_trace)
    assert len(myfun._self_trace) == 1

    # tracing a method (careful with instances and call time !)

    class TraceTest:
        @traced()
        def myfun(self, a = 39):
            return a + 3

    tt = TraceTest()
    assert tt.myfun(48) == 51

    print (tt.myfun._self_trace)
    assert len(tt.myfun._self_trace) == 1


    # tr = agenttrace()
    #
    # sig = inspect.signature(myfun)
    # bound_args = sig.bind(48)
    # bound_args.apply_defaults()
    #
    # # putting the call in the trace
    # tr[bound_args] = myfun(*bound_args.args, **bound_args.kwargs)
    #
    # # retrieving the call by passing parameters again
    # assert tr[48,] == 53, f"Unexpected value stored in trace {tr[(48,)]}"







