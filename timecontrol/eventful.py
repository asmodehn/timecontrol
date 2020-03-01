import asyncio
import inspect
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, MINYEAR
import typing
from result import Result

# TODO : different kinds of !structured! log / dataframes, etc.

import asyncio
from collections import OrderedDict
from datetime import datetime, MINYEAR, timedelta
import inspect

import typing
import wrapt
import functools


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


@dataclass(frozen=True, init=False)
class CommandCalled:
    # TODO : more time representation
    timestamp: typing.Union[int, datetime]
    bound_args: typing.FrozenSet  # we need a frozenset here to be hashable

    def __init__(self, bound_arguments: inspect.BoundArguments, timestamp: typing.Union[int, datetime] = None):
        # TODO : maybe apply default here to make sure...
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)
        object.__setattr__(self, "timestamp", timestamp)
        # we change bound arguments to a frozendict (to be hashable)
        object.__setattr__(self, "bound_args", frozendict(bound_arguments.arguments))
        # This should be all we need. and we don't need mutability as it is already final
        # Also order doesnt matter as they are already bound to a name (right ?)


@dataclass(frozen=True, init=False)
class CommandReturned:
    # TODO : more time representation
    timestamp: typing.Union[int, datetime]
    # we use result here to keep return "in-band". we don't want "out-of-band" exceptions breaking the control flow...
    result: Result

    def __init__(self, result: Result, timestamp: typing.Union[int, datetime] = None):
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)
        object.__setattr__(self, "timestamp", timestamp)
        object.__setattr__(self, "result", result)


@dataclass(frozen=True, init=False)
class CommandReturnedLate(CommandReturned):
    # TODO : more time representation
    timestamp_bound: typing.Union[int, datetime]

    def __init__(self, result: Result, timestamp_bound: typing.Union[int, datetime], timestamp: typing.Union[int, datetime] = None):
        object.__setattr__(self, "timestamp_bound", timestamp_bound)
        super(CommandReturnedLate, self).__init__(result=result, timestamp=timestamp)


Event = typing.Union[CommandCalled, CommandReturned, CommandReturnedLate]


TimePeriod = typing.Union[timedelta, int]
TimePoint = typing.Union[datetime, int]


def default_sync_sleeper(delay: TimePeriod):
    if isinstance(delay, timedelta):
        time.sleep(delay.seconds)
    else:
        time.sleep(delay)


def default_async_sleeper(delay: TimePeriod):
    if isinstance(delay, timedelta):
        asyncio.sleep(delay=delay.seconds)
    else:
        asyncio.sleep(delay=
                      delay)


def eventful(#TODO : pass event store in decorator.
        #: https://en.wikipedia.org/wiki/Rate_limiting
        # But this is expressed in time units (minimal guaranteed "no-call" period)
        ratelimit: typing.Optional[TimePeriod] = None,

        #: https://en.wikipedia.org/wiki/Temporal_resolution
        timeframe: typing.Optional[TimePeriod] = None,

        timer: typing.Callable[[], TimePoint] = datetime.now,
        sleeper: typing.Callable[[TimePeriod], None]=None):
    """
        An Eventful Generator.
        This wraps a python pydef definition into a generator of events

        >>> def inc(a: int):
        ...    return a+1
        >>> einc = generator()(inc)

        >>> print(einc)  # doctest: +ELLIPSIS
        <function inc at 0x...>
        >>> for e in einc(41):
        ...    print(e)  # doctest: +ELLIPSIS
        CommandCalled(timestamp=datetime.datetime(...), bound_args=frozenset({('a', 41)}))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(42))

        Note it works as well for generators, wrapping yielded values in events:
        This wraps a python generator definition in another generator, timing values yielded.

        >>> def inc(a: int):
        ...    yield a+1
        ...    yield a+2
        ...    yield a+3

        >>> einc = generator()(inc)

        >>> print(einc)  # doctest: +ELLIPSIS
        <__main__.EventfulDef object at 0x...>
        >>> for e in einc(41):
        ...    print(e)  # doctest: +ELLIPSIS
        CommandCalled(timestamp=datetime.datetime(...), bound_args=frozenset({('a', 41)}))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(42))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(43))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(44))

        https://docs.python.org/3/reference/expressions.html#yield-expressions

        The async version works similarly.

        >>> import asyncio
        >>> async def inc(a: int):
        ...     await asyncio.sleep(1)
        ...     return a+1

        >>> ainc = generator()(inc)

        >>> print(ainc)  # doctest: +ELLIPSIS
        <__main__.AsyncEventfulDef object at 0x...>

        Here we need an coroutine to run it, since python root level is synchronous:
        >>> async def arun(agen):
        ...     async for e in ainc(41):
        ...         print(e)
        >>> asyncio.run(arun(agen=ainc))  # doctest: +ELLIPSIS
        CommandCalled(timestamp=datetime.datetime(...), bound_args=frozenset({('a', 41)}))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(42))


        This works as well for async generator:
        This wraps a python async definition in an async generator, timing call and return.
        >>> import asyncio
        >>> async def inc(a: int):
        ...     await asyncio.sleep(1)
        ...     yield a+1
        ...     yield a+2
        ...     yield a+3

        >>> ainc = generator()(inc)

        >>> print(ainc)  # doctest: +ELLIPSIS
        <__main__.AsyncEventfulDef object at 0x...>

        Here we need an coroutine to run it, since python root level is synchronous:
        >>> async def arun(agen):
        ...     async for e in ainc(41):
        ...         await asyncio.sleep(1)
        ...         print(e)
        >>> asyncio.run(arun(agen=ainc))  # doctest: +ELLIPSIS
        CommandCalled(timestamp=datetime.datetime(...), bound_args=frozenset({('a', 41)}))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(42))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(43))
        CommandReturned(timestamp=datetime.datetime(...), result=Ok(44))

        Ref : https://docs.python.org/3/reference/expressions.html#asynchronous-generator-functions


        Note : attempting to split the call/return couple seems to lead to a different, more functional,
         more elementary/low-level design, which doesn't seem to be a good fit for python.
        It is not suitable in our case, especially since this aims to be used as often as possible...
        Therefore we accumulated a bunch of code in here, also with code related to time and synchronization.

        Note : Using a class to implement the decorator doesnt seem to fit our usecase,
        as we want "as pythonic as possible" usage to not trip up the user of @generator.
        We aim to be as general as possible, hence both unbound and bound functions and methods are supported here.
        """



    _last = timer()
    # Setting last as now, to prevent accidental bursts on creation.

    _inner_last = datetime(year=MINYEAR, month=1, day=1)
    # Setting last as long time ago, to force speedup on creation.

    def _call_event(bound_args: inspect.BoundArguments) -> typing.Union[CommandCalled, timedelta]:

        nonlocal _last

        if ratelimit:
            # Measure time
            now = timer()

            # sleep if needed (this can be addressed locally)
            if now - _last < ratelimit:
                # Call too fast.
                # sleeps expected time period - already elapsed time
                return ratelimit - (now - _last)
            else:
                _last = now

        # We have to duplicate bound arguments here, since that type is not serializable...
        return CommandCalled(timestamp=timer(), bound_arguments=bound_args)

    def _result_event(e) -> CommandReturned:

        nonlocal _inner_last

        # Measure time
        inner_now = timer()

        result = Result.Ok(e)
        if timeframe and inner_now - _inner_last > timeframe:
            # Call too slow
            # Log exception (we cannot do anything locally - it is up to the scheduler who scheduled us)
            ret = CommandReturnedLate(result=result, timestamp_bound=_inner_last + timeframe,
                                      timestamp=timer())
        else:
            ret = CommandReturned(result=result, timestamp=timer())

        # need to do that after the > period check !
        _inner_last = inner_now

        return ret

    def decorator(wrapped):
        nonlocal sleeper

        _eventlog = OrderedDict()

        @wrapt.decorator
        async def async_eventful_generator(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_async_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time
                instance.eventlog = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            call_event = _call_event(bound_args=bound_args)
            _eventlog[call_event.timestamp] = call_event

            # yield call_event

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                # Note this execution flow is linear (one or more result).
                async for e in res:
                    # Note: the loop being at this level, shows that this generator
                    # should not access resources "out of system border".
                    # In this case everything is supposedly "internal" (ie in python interpreter process).
                    res_evt = _result_event(e)
                    _eventlog[res_evt.timestamp] = res_evt
                    yield e
                    # Note: this internally can return result with a "late" result type.
                    # This is a signal for an external system to do something (nothing can be done in here)
                return

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result, timestamp=timer())
                _eventlog[res_evt.timestamp] = res_evt
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        async def async_eventful_function(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_async_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time
                instance.eventlog = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            call_event = _call_event(bound_args=bound_args)
            _eventlog[call_event.timestamp] = call_event

            # yield call_event

            try:
                res = await wrapped(*bound_args.args, **bound_args.kwargs)

                # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                res_evt = _result_event(res)
                _eventlog[res_evt.timestamp] = res_evt
                return res

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result, timestamp=timer())
                _eventlog[res_evt.timestamp] = res_evt
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        def eventful_generator(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_sync_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time)
                instance.eventlog = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            call_event = _call_event(bound_args=bound_args)

            while isinstance(call_event, (int, timedelta)):  # the intent is to sleep
                _sleeper(call_event)
                call_event = _call_event(bound_args=bound_args)

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                _eventlog[call_event.timestamp] = call_event
                yield call_event  # yielding after the call !

                # Note this execution flow is linear (one or more result).
                for e in res:
                    # Note: the loop being at this level, shows that this generator
                    # should not access resources "out of system border".
                    # In this case everything is supposedly "internal" (ie in python interpreter process).
                    res_evt = _result_event(e)
                    _eventlog[res_evt.timestamp] = res_evt
                    yield e
                    # Note: this internally can return result with a "late" result type.
                    # This is a signal for an external system to do something (nothing can be done in here)
                return
            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result, timestamp=timer())
                _eventlog[res_evt.timestamp] = res_evt
                raise  # to propagate any unexpected exception (the usual expected behavior)

        @wrapt.decorator
        def eventful_function(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_sync_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time
                instance.eventlog = _eventlog

            sig = inspect.signature(wrapped)
            # checking arguments binding early
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            call_event = _call_event(bound_args=bound_args)

            while isinstance(call_event, (int, timedelta)):  # the intent is to sleep
                _sleeper(call_event)
                call_event = _call_event(bound_args=bound_args)

            try:
                res = wrapped(*bound_args.args, **bound_args.kwargs)

                _eventlog[call_event.timestamp] = call_event

                # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                res_evt = _result_event(res)
                _eventlog[res_evt.timestamp] = res_evt
                return res

            except Exception as exc:
                result = Result.Err(exc)
                res_evt = CommandReturned(result=result, timestamp=timer())
                _eventlog[res_evt.timestamp] = res_evt
                raise  # to propagate any unexpected exception (the usual expected behavior)


        if inspect.isclass(wrapped):
            #TODO : store log in the meta class ???
            wrap = eventful_function(wrapped)  # wrapping the init of the class
            # the log will be set on the instance on the first call (cannot be on the class)

        # checking for async first, to avoid too much if-nesting
        elif inspect.isasyncgenfunction(wrapped):  # for some reason asyncgen is not a coroutine... (py3.7)
            wrap = async_eventful_generator(wrapped)

        elif inspect.iscoroutinefunction(wrapped):
            wrap = async_eventful_function(wrapped)

        # then the more general case
        elif inspect.isfunction(wrapped):
            if inspect.isgeneratorfunction(wrapped):
                wrap = eventful_generator(wrapped)
            else:
                wrap = eventful_function(wrapped)

        # did we forget any usecase ?
        else:
            raise NotImplementedError(f"eventful doesnt support decorating {wrapped}")

        if not inspect.ismethod(wrapped):
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



# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()


if __name__ == '__main__':

    @eventful()
    def function():
        return 42


    @eventful()
    def generator():
        yield 42
        yield 43
        yield 44


    @eventful()
    async def async_function():
        await asyncio.sleep(1)
        return 42


    @eventful()
    async def async_generator():
        await asyncio.sleep(1)
        yield 42
        await asyncio.sleep(1)
        yield 43
        await asyncio.sleep(1)
        yield 44


    print("function")
    print(function())
    for e in function.eventlog.values():
        print(e)

    print("generator")
    for r in generator():
        print(r)

    for e in generator.eventlog.values():
        print(e)

    async def async_runtime():
        print("async function")
        print(await async_function())

        for e in function.eventlog.values():
            print(e)

        print("async generator")
        async for r in async_generator():
            print(r)

        for e in async_generator.eventlog.values():
            print(e)

    asyncio.run(async_runtime())

