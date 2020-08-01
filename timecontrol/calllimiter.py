import asyncio
import inspect


# Note the dual concept is still to be determined... (something speeding up scheduler/eventloop somehow...)
import time
from datetime import datetime, MINYEAR, timedelta

import typing
import wrapt

from timecontrol.eventful import TimePeriod, TimePoint


def calllimiter(# TODO pass log:  = None,  Maybe pass a function / async callable instead ?
        #: https://en.wikipedia.org/wiki/Rate_limiting
        # But this is expressed in time units (minimal guaranteed "no-call" period)
        ratelimit: typing.Optional[TimePeriod] = None,

        #: https://en.wikipedia.org/wiki/Temporal_resolution
        #timeframe: typing.Optional[TimePeriod] = None,
        # Not useful here, only for loopaccelerator

        timer: typing.Callable[[], TimePoint] = datetime.now,
        sleeper: typing.Callable[[TimePeriod], None]=None):

    _last = timer()
    # Setting last as now, to prevent accidental bursts on creation.

    _inner_last = datetime(year=MINYEAR, month=1, day=1)
    # Setting last as long time ago, to force speedup on creation.

    def decorator(wrapper):
        nonlocal sleeper

        @wrapt.decorator
        def calllimited_function(wrapped, instance, args, kwargs):

            nonlocal _last

            if ratelimit:
                # Measure time
                now = timer()

                # print(f"{now} - {_last} = {now - _last}")
                # sleep if needed (this can be addressed locally)
                if now - _last < ratelimit:
                    # Call too fast.
                    sleeptime = (ratelimit - (now - _last))
                    if isinstance(sleeptime, timedelta):
                        sleeptime=sleeptime.total_seconds()
                    # print(f"sleeps for {sleeptime}")
                    # sleeps expected time period - already elapsed time
                    sleeper(sleeptime)

                _last = timer()

            return wrapped(*args, **kwargs)

        @wrapt.decorator
        async def async_calllimited_function(wrapped, instance, args, kwargs):

            nonlocal _last
            # TODO : we need an asyncio.Lock here. This is meaningless if we get concurrent calls...
            if ratelimit:
                # Measure time
                now = timer()

                # print(f"{now} - {_last} = {now - _last}")
                # sleep if needed (this can be addressed locally)
                if now - _last < ratelimit:
                    # Call too fast.
                    sleeptime = (ratelimit - (now - _last))
                    if isinstance(sleeptime, timedelta):
                        sleeptime=sleeptime.total_seconds()
                    # print(f"sleeps for {sleeptime}")
                    # sleeps expected time period - already elapsed time
                    await sleeper(sleeptime)

                _last = timer()

            return await wrapped(*args, **kwargs)

        # Note : in this decorator generators or classes are not considered...
        # it throttles only the usual call.

        # checking for async first, to avoid too much if-nesting
        if inspect.iscoroutinefunction(wrapper):
            if sleeper is None:
                sleeper = asyncio.sleep
            wrap = async_calllimited_function(wrapper)

            # then the more general case
        elif inspect.isfunction(wrapper) or inspect.ismethod(wrapper):
            if sleeper is None:
                sleeper = time.sleep
            wrap = calllimited_function(wrapper)

            # did we forget any usecase ?
        else:
            raise NotImplementedError(f"eventful doesnt support decorating {wrapper}")

        return wrap
    return decorator


if __name__ == '__main__':

    @calllimiter(ratelimit=timedelta(seconds=2))
    def printer(*args, **kwargs):
        print(f"{datetime.now()} : {args}, {kwargs}")

    now = datetime.now()
    while datetime.now() - now < timedelta(seconds=10):
        printer("the", "answer", "is", 42, answer=42)


    @calllimiter(ratelimit=timedelta(seconds=2))
    async def async_printer(*args, **kwargs):
        print(f"{datetime.now()} : {args}, {kwargs}")

    async def async_runner():
        now = datetime.now()
        while datetime.now() - now < timedelta(seconds=10):
            await async_printer("the", "async", "answer", "is", 42, async_answer=42)

    asyncio.run(async_runner())
