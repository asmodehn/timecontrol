import asyncio
from collections import OrderedDict
from datetime import datetime, MINYEAR, timedelta
import inspect

import typing
import wrapt
import functools


from result import Result

from timecontrol.eventful import (
    TimePeriod, TimePoint, default_async_sleeper, default_sync_sleeper, CommandCalled,
    CommandReturned,
    CommandReturnedLate,
)


def eventful(#TODO : pass event store in decorator.
        #: https://en.wikipedia.org/wiki/Rate_limiting
        # But this is expressed in time units (minimal guaranteed "no-call" period)
        ratelimit: typing.Optional[TimePeriod] = None,

        #: https://en.wikipedia.org/wiki/Temporal_resolution
        timeframe: typing.Optional[TimePeriod] = None,

        timer: typing.Callable[[], TimePoint] = datetime.now,
        sleeper: typing.Callable[[TimePeriod], None]=None):

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
        async def async_eventful_wrapper(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_async_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time
                instance.eventlog = _eventlog

            try:  # call time

                sig = inspect.signature(wrapped)
                # checking arguments binding early
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                call_event = _call_event(bound_args=bound_args)
                _eventlog[call_event.timestamp] = call_event

                yield call_event

                try:
                    res = wrapped(*bound_args.args, **bound_args.kwargs)

                    if inspect.isasyncgen(res):
                        # Note this execution flow is linear (one or more result).
                        async for e in res:
                            # Note: the loop being at this level, shows that this generator
                            # should not access resources "out of system border".
                            # In this case everything is supposedly "internal" (ie in python interpreter process).
                            res_evt = _result_event(e)
                            _eventlog[res_evt.timestamp] = res_evt
                            yield res_evt
                            # Note: this internally can return result with a "late" result type.
                            # This is a signal for an external system to do something (nothing can be done in here)
                    else:
                        # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                        #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                        res_evt = _result_event(await res)
                        _eventlog[res_evt.timestamp] = res_evt
                        yield res_evt
                    return

                except Exception as exc:
                    result = Result.Err(exc)
                    res_evt = CommandReturned(result=result, timestamp=timer())
                    _eventlog[res_evt.timestamp] = res_evt
                    yield res_evt
                    raise  # to propagate any unexpected exception (the usual expected behavior)

            except GeneratorExit as ge:
                raise  # Nothing to cleanup, just end it right now.

        @wrapt.decorator
        def eventful_wrapper(wrapped, instance, args, kwargs):

            # This is here only to allow dependency injection for testing
            _sleeper = default_sync_sleeper if sleeper is None else sleeper

            if instance is not None and not hasattr(instance, "eventlog"):
                # then the log should be here (but only assign the first time
                instance.eventlog = _eventlog

            try:  # call time

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

                    if inspect.isgenerator(res):
                        # Note this execution flow is linear (one or more result).
                        for e in res:
                            # Note: the loop being at this level, shows that this generator
                            # should not access resources "out of system border".
                            # In this case everything is supposedly "internal" (ie in python interpreter process).
                            res_evt = _result_event(e)
                            _eventlog[res_evt.timestamp] = res_evt
                            yield res_evt
                            # Note: this internally can return result with a "late" result type.
                            # This is a signal for an external system to do something (nothing can be done in here)
                    else:
                        # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                        #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                        res_evt = _result_event(res)
                        _eventlog[res_evt.timestamp] = res_evt
                        yield res_evt
                    return
                except Exception as exc:
                    result = Result.Err(exc)
                    res_evt = CommandReturned(result=result, timestamp=timer())
                    _eventlog[res_evt.timestamp] = res_evt
                    yield res_evt
                    raise  # to propagate any unexpected exception (the usual expected behavior)
            except GeneratorExit as ge:
                raise  # Nothing to cleanup, just end it right now.)

        if inspect.isclass(wrapped):
            #TODO : in the meta class ???
            raise NotImplementedError

        elif inspect.ismethod(wrapped):
            wrap = eventful_wrapper(wrapped)
            # the log will be set on the instance on the first call (cannot be on the method)

        elif inspect.iscoroutinefunction(wrapped):
            wrap = async_eventful_wrapper(wrapped)
            wrap.log = _eventlog
        else:
            wrap = eventful_wrapper(wrapped)
            wrap.log = _eventlog
            # TODO : patch wrap to add a logstream.
        return wrap
    return decorator


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


if __name__ == '__main__':
    print("function")
    # print(function())
    for e in function():
        print(e)

    print("generator")
    for r in generator():
        print(r)

    for e in generator:
        print(e)

    async def async_runtime():
        print("async function")
        print(await async_function())

        for e in function:
            print(e)

        print("async generator")
        async for r in async_generator():
            print(r)

        for e in function:
            print(e)

    asyncio.run(async_runtime())
