import asyncio
import inspect
import time
import typing
from datetime import MINYEAR, datetime, timedelta

import wrapt

from timecontrol.calllimiter import TimePeriod, TimePoint


def callscheduler(  # TODO pass log:  = None,  Maybe pass a function / async callable instead ?
    #: https://en.wikipedia.org/wiki/Rate_limiting
    # But this is expressed in time units (minimal guaranteed "no-call" period)
    ratelimit: typing.Optional[TimePeriod] = None,
    #: https://en.wikipedia.org/wiki/Temporal_resolution
    # timeframe: typing.Optional[TimePeriod] = None,
    # Not useful here, only for loopaccelerator
    timer: typing.Callable[[], TimePoint] = datetime.now,
    sleeper: typing.Callable[[TimePeriod], None] = None,
):

    _last = timer() - ratelimit
    # Setting last as now - ratelimit, to allow immediate trigger on creation.

    _inner_last = datetime(year=MINYEAR, month=1, day=1)
    # Setting last as long time ago, to force speedup on creation.

    def decorator(wrapper):
        nonlocal sleeper

        @wrapt.decorator
        def callscheduled_function(wrapped, instance, args, kwargs):

            nonlocal _last

            while ratelimit:  # TODO : find a way to stop/cancel this ?
                # Measure time
                now = timer()

                # print(f"{now} - {_last} = {now - _last}")
                # sleep if needed (this can be addressed locally)
                sleeptime = ratelimit - (
                    (now - _last) - ratelimit
                )  # sleep time should be less than ratelimit
                if isinstance(sleeptime, timedelta):
                    sleeptime = sleeptime.total_seconds()

                print(f"sleeps for {sleeptime}")
                # sleeps expected time period - already elapsed time
                sleeper(sleeptime)

                if timer() - _last >= ratelimit:
                    # Call too slow. calling now
                    yield wrapped(*args, **kwargs)
                    _last = timer()

            # return None mandatory for generators

        @wrapt.decorator
        async def async_calllimited_function(wrapped, instance, args, kwargs):

            nonlocal _last
            # TODO : we need a way to deal with concurrent calls here ... maybe sharing the timers ?
            while ratelimit:
                # TODO : another possibility is to trampoline here by scheduling a task in the current eventloop...
                #  It would allow debug and cancelling in the usual ascynio fashion...
                # Measure time
                now = timer()

                # print(f"{now} - {_last} = {now - _last}")
                # sleep if needed (this can be addressed locally)
                # need to sleep to wait next calltime
                sleeptime = ratelimit - (
                    (now - _last) - ratelimit
                )  # sleep time should be less than ratelimit
                if isinstance(sleeptime, timedelta):
                    sleeptime = sleeptime.total_seconds()

                print(f"sleeps for {sleeptime}")
                # sleeps expected time period - already elapsed time
                await sleeper(sleeptime)

                if now - _last >= ratelimit:
                    yield await wrapped(*args, **kwargs)
                    _last = timer()

            # return None mandatory for generators

        # Note : in this decorator generators or classes are not considered...
        # it loop-schedule only the usual call.

        # checking for async first, to avoid too much if-nesting
        if inspect.iscoroutinefunction(wrapper):
            if sleeper is None:
                sleeper = asyncio.sleep
            wrap = async_calllimited_function(wrapper)

            # then the more general case
        elif inspect.isfunction(wrapper) or inspect.ismethod(wrapper):
            if sleeper is None:
                sleeper = time.sleep
            wrap = callscheduled_function(wrapper)

            # did we forget any usecase ?
        else:
            raise NotImplementedError(f"eventful doesnt support decorating {wrapper}")

        return wrap  # TODO : maybe return a scheduled task (stream ?) instead ??

    return decorator


if __name__ == "__main__":

    # ENABLE one or the other...

    # @callscheduler(ratelimit=timedelta(seconds=2))
    # def printer(*args, **kwargs):
    #     print(f"{datetime.now()} : {args}, {kwargs}")
    #
    # for call in printer("the", "answer", "is", 42, answer=42):
    #     print(call)
    #     pass  # no printing, it would duplicate the inner call

    @callscheduler(ratelimit=timedelta(seconds=2))
    async def async_printer(*args, **kwargs):
        print(f"{datetime.now()} : {args}, {kwargs}")

    async def async_runner():

        async for call in async_printer("the", "async", "answer", "is", 42, answer=42):
            print(call)
            pass  # no printing, it would duplicate the inner call

    asyncio.run(async_runner())
