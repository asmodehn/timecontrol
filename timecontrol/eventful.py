import asyncio
import inspect
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, MINYEAR
import typing
from result import Result

# TODO : different kinds of !structured! log / dataframes, etc.

import asyncio
from collections import OrderedDict, Hashable
from datetime import datetime, MINYEAR, timedelta
import inspect

import typing
import wrapt
import functools

from timecontrol.events import CommandCalled, CommandReturned, CommandReturnedLate, frozendict
from timecontrol.eventstore import EventStore, eventstore

TimePeriod = typing.Union[timedelta, int]
TimePoint = typing.Union[datetime, int]  # how about float ? time.time() -> float


# def default_sync_sleeper(delay: TimePeriod):
#     if isinstance(delay, timedelta):
#         time.sleep(delay.seconds)
#     else:
#         time.sleep(delay)
#
#
# def default_async_sleeper(delay: TimePeriod):
#     if isinstance(delay, timedelta):
#         asyncio.sleep(delay=delay.seconds)
#     else:
#         asyncio.sleep(delay=
#                       delay)


def eventful(
        # need a generator which consumes events... (can aggregate them, transmit them, etc.)
        event_eradicator: typing.Optional[EventStore] = None,

        #: https://en.wikipedia.org/wiki/Rate_limiting
        # But this is expressed in time units (minimal guaranteed "no-call" period)
        # ratelimit: typing.Optional[TimePeriod] = None,

        #: https://en.wikipedia.org/wiki/Temporal_resolution
        # timeframe: typing.Optional[TimePeriod] = None,

        #timer: typing.Callable[[], TimePoint] = datetime.now,
        #sleeper: typing.Callable[[TimePeriod], None]=None
        ):
    """
    An Eventful Generator.
    This wraps a python pydef definition into a generator of events

    >>> def inc(a: int):
    ...    return a+1
    >>> einc = eventful()(inc)

    >>> print(einc)  # doctest: +ELLIPSIS
    <function inc at 0x...>
    >>> einc(41)
    42
    >>> for ti, e in einc.eventlog:
    ...    print(e)  # doctest: +ELLIPSIS
    EventCounter<CommandCalled(bound_args=frozenset({('a', 41)})): 1, CommandReturned(result=Ok(42)): 1>

    Note it works as well for generators, wrapping yielded values in events:
    This wraps a python generator definition in another generator, timing values yielded.

    >>> def inc(a: int):
    ...    yield a+1
    ...    yield a+2
    ...    yield a+3

    >>> einc = eventful()(inc)

    >>> print(einc)  # doctest: +ELLIPSIS
    <function inc at 0x...>
    >>> for e in einc(41):
    ...    print(e)
    42
    43
    44
    >>> for ti, e in einc.eventlog:
    ...    print(e)  # doctest: +ELLIPSIS
    EventCounter<CommandCalled(bound_args=frozenset({('a', 41)})): 1, CommandReturned(result=Ok(42)): 1, CommandReturned(result=Ok(43)): 1, CommandReturned(result=Ok(44)): 1>

    https://docs.python.org/3/reference/expressions.html#yield-expressions

    The async version works similarly.

    >>> import asyncio
    >>> async def inc(a: int):
    ...     await asyncio.sleep(1)
    ...     return a+1

    >>> ainc = eventful()(inc)

    >>> print(ainc)  # doctest: +ELLIPSIS
    <function inc at 0x...>

    Here we need an coroutine to run it, since python root level is synchronous:
    >>> async def arun():
    ...     print(await ainc(41))
    ...     for ti, e in ainc.eventlog:
    ...         print(e)
    >>> asyncio.run(arun())  # doctest: +ELLIPSIS
    42
    EventCounter<>
    EventCounter<CommandCalled(bound_args=frozenset({('a', 41)})): 1, CommandReturned(result=Ok(42)): 1>


    This works as well for async generator:
    This wraps a python async definition in an async generator, timing call and return.
    >>> import asyncio
    >>> async def inc(a: int):
    ...     await asyncio.sleep(1)
    ...     yield a+1
    ...     yield a+2
    ...     yield a+3

    >>> ainc = eventful()(inc)

    >>> print(ainc)  # doctest: +ELLIPSIS
    <function inc at 0x...>

    Here we need an coroutine to run it, since python root level is synchronous:
    >>> async def arun():
    ...     async for e in ainc(41):
    ...         await asyncio.sleep(1)
    ...         print(e)
    ...     for ti, e in ainc.eventlog:
    ...         print(e)
    >>> asyncio.run(arun())  # doctest: +ELLIPSIS
    42
    43
    44
    EventCounter<>
    EventCounter<CommandReturned(result=Ok(44)): 1>
    EventCounter<CommandReturned(result=Ok(43)): 1>
    EventCounter<CommandCalled(bound_args=frozenset({('a', 41)})): 1, CommandReturned(result=Ok(42)): 1>

    The last empty event counter is there for the current time frame, and hasnt been discarded just yet...

    Ref : https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions


    Note : attempting to split the call/return couple seems to lead to a different, more functional,
     more elementary/low-level design, which doesn't seem to be a good fit for python.
    It is not suitable in our case, especially since this aims to be used as often as possible...
    Therefore we accumulated a bunch of code in here, also with code related to time and synchronization.

    Note : Using a class to implement the decorator doesnt seem to fit our usecase,
    as we want "as pythonic as possible" usage to not trip up the user of @generator.
    We aim to be as general as possible, hence both unbound and bound functions and methods are supported here.
    """

    _eventlog = eventstore() if event_eradicator is None else event_eradicator

    # _last = timer()
    # # Setting last as now, to prevent accidental bursts on creation.
    #
    # _inner_last = datetime(year=MINYEAR, month=1, day=1)
    # Setting last as long time ago, to force speedup on creation.

    def _call_event(bound_args: inspect.BoundArguments) -> typing.Union[CommandCalled, timedelta]:
        # TODO : remove rate limiter from here, user can use the calllimiter decorator...
        # nonlocal _last
        # TODO : before cleaning this up, we need to test it thoroughly...
        # if ratelimit:
        #     # Measure time
        #     now = timer()
        #
        #     # sleep if needed (this can be addressed locally)
        #     if now - _last < ratelimit:
        #         # Call too fast.
        #         # sleeps expected time period - already elapsed time
        #         return ratelimit - (now - _last)
        #     else:
        #         _last = now

        # We have to duplicate bound arguments here, since that type is not serializable...
        return CommandCalled(bound_arguments=bound_args)

    def _result_event(e) -> CommandReturned:

        # nonlocal _inner_last
        #
        # # Measure time
        # inner_now = timer()

        #CAREFUL HERE : order is important...
        if isinstance(e, Hashable):  # same as checking for "__hash__" attribute...
            result = Result.Ok(e)
        elif isinstance(e, dict):
            result = Result.Ok(frozendict(e))
        else:
            raise RuntimeError(f"{e} is not hashable")  # error early

        # if timeframe and inner_now - _inner_last > timeframe:
        #     # Call too slow
        #     # Log exception (we cannot do anything locally - it is up to the scheduler who scheduled us)
        #     # => maybe useless here ?
        #     ret = CommandReturnedLate(result=result)
        # else:
        ret = CommandReturned(result=result)

        # need to do that after the > period check !
        # _inner_last = inner_now

        return ret

    def decorator(wrapper):
        # nonlocal sleeper

        @wrapt.decorator
        async def async_eventful_generator(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            # _sleeper = default_async_sleeper if sleeper is None else sleeper

            if instance is not None:
                if not hasattr(instance, "eventlog"):
                    instance.eventlog = dict()
                # only assign the first time
                if wrapped.__name__ not in instance.eventlog:
                    instance.eventlog[wrapped.__name__] = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            event_logger = _eventlog()
            event_logger.send(None)  # note we ignore hte current timeframe and starting counter

            # Storing event in log
            call_event = _call_event(bound_args=bound_args)
            event_logger.send(call_event)

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                # Note this execution flow is linear (one or more result).
                async for e in res:
                    # Note: the loop being at this level, shows that this generator
                    # should not access resources "out of system border".
                    # In this case everything is supposedly "internal" (ie in python interpreter process).
                    res_evt = _result_event(e)
                    event_logger.send(res_evt)  # storing event in log
                    yield e
                    # Note: this internally can return result with a "late" result type.
                    # This is a signal for an external system to do something (nothing can be done in here)
                return

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result)
                event_logger.send(res_evt)  # storing event in log
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        async def async_eventful_function(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            # _sleeper = default_async_sleeper if sleeper is None else sleeper

            if instance is not None:
                if not hasattr(instance, "eventlog"):
                    instance.eventlog = dict()
                # only assign the first time
                if wrapped.__name__ not in instance.eventlog:
                    instance.eventlog[wrapped.__name__] = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            event_logger = _eventlog()
            event_logger.send(None)  # note we ignore hte current timeframe and starting counter

            call_event = _call_event(bound_args=bound_args)
            # TODO : handle rate limitation !
            event_logger.send(call_event)  # storing event in log

            # yield call_event

            try:
                res = await wrapped(*bound_args.args, **bound_args.kwargs)

                # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                res_evt = _result_event(res)
                event_logger.send(res_evt)  # storing event in log
                return res

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result)
                event_logger.send(res_evt)  # storing event in log
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        def eventful_generator(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            # _sleeper = default_sync_sleeper if sleeper is None else sleeper

            if instance is not None:
                if not hasattr(instance, "eventlog"):
                    instance.eventlog = dict()
                # only assign the first time
                if wrapped.__name__ not in instance.eventlog:
                    instance.eventlog[wrapped.__name__] = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            event_logger = _eventlog()
            event_logger.send(None)  # note we ignore hte current timeframe and starting counter

            call_event = _call_event(bound_args=bound_args)

            # while isinstance(call_event, (int, timedelta)):  # the intent is to sleep
            #     _sleeper(call_event)
            #     call_event = _call_event(bound_args=bound_args)

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                event_logger.send(call_event) # storing event in log
                # yield call_event  # yielding after the call !

                # Note this execution flow is linear (one or more result).
                for e in res:
                    # Note: the loop being at this level, shows that this generator
                    # should not access resources "out of system border".
                    # In this case everything is supposedly "internal" (ie in python interpreter process).
                    res_evt = _result_event(e)
                    event_logger.send(res_evt)  # storing event in log
                    yield e
                    # Note: this internally can return result with a "late" result type.
                    # This is a signal for an external system to do something (nothing can be done in here)
                return
            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result)
                event_logger.send(res_evt)  # storing event in log
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        def eventful_function(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            # _sleeper = default_sync_sleeper if sleeper is None else sleeper

            if inspect.ismethod(wrapped):
                if not instance is None:
                    if not hasattr(instance, "eventlog"):  # usual instance method
                        instance.eventlog = dict()
                    # only assign the first time
                    if wrapped.__name__ not in instance.eventlog:
                        instance.eventlog[wrapped.__name__] = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            event_logger = _eventlog()
            event_logger.send(None)  # note we ignore hte current timeframe and starting counter

            call_event = _call_event(bound_args=bound_args)

            # while isinstance(call_event, (int, timedelta)):  # the intent is to sleep
            #     _sleeper(call_event)
            #     call_event = _call_event(bound_args=bound_args)

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                event_logger.send(call_event)  # storing event in log

                # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                res_evt = _result_event(res)
                event_logger.send(res_evt)  # storing event in log
                return res

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result)
                event_logger.send(res_evt)  # storing event in log
                raise  # to propagate any unexpected exception (the usual expected behavior)

        if inspect.isclass(wrapper):
            #TODO : store log in the meta class ???
            wrap = eventful_function(wrapper)  # wrapping the init of the class
            # the log will be set on the instance on the first call (cannot be on the class)

        # checking for async first, to avoid too much if-nesting
        elif inspect.isasyncgenfunction(wrapper):  # for some reason asyncgen is not a coroutine... (py3.7)
            wrap = async_eventful_generator(wrapper)

        elif inspect.iscoroutinefunction(wrapper):
            wrap = async_eventful_function(wrapper)

        # then the more general case
        elif inspect.isfunction(wrapper) or inspect.ismethod(wrapper):
            if inspect.isgeneratorfunction(wrapper):
                wrap = eventful_generator(wrapper)
            else:
                wrap = eventful_function(wrapper)

        # did we forget any usecase ?
        else:
            raise NotImplementedError(f"eventful doesnt support decorating {wrapper}")

        if not inspect.ismethod(wrapper):
            wrap.eventlog = _eventlog
        # else the log will be set on the instance on the first call (cannot be on the method)

        return wrap
    return decorator


# TODO : redesign this module code to keep the usual wrapped "thing" behavior,
#  but only add logging events to something else...
# @eventful(log=MyLog())
# def myfun(args):
#     does smthg
#

# TODO : slowly split
#  - timestamping
#  - logging
#  - event generation



if __name__ == '__main__':
    import doctest
    doctest.testmod(verbose=True)


# if __name__ == '__main__':
#
#     @eventful()
#     def function():
#         return 42
#
#
#     @eventful()
#     def generator():
#         yield 42
#         yield 43
#         yield 44
#
#
#     @eventful()
#     async def async_function():
#         await asyncio.sleep(1)
#         return 42
#
#
#     @eventful()
#     async def async_generator():
#         await asyncio.sleep(1)
#         yield 42
#         await asyncio.sleep(1)
#         yield 43
#         await asyncio.sleep(1)
#         yield 44
#
#
#     print("function")
#     print(function())
#     for e in function.eventlog.values():
#         print(e)
#
#     print("generator")
#     for r in generator():
#         print(r)
#
#     for e in generator.eventlog.values():
#         print(e)
#
#     async def async_runtime():
#         print("async function")
#         print(await async_function())
#
#         for e in function.eventlog.values():
#             print(e)
#
#         print("async generator")
#         async for r in async_generator():
#             print(r)
#
#         for e in async_generator.eventlog.values():
#             print(e)
#
#     asyncio.run(async_runtime())

