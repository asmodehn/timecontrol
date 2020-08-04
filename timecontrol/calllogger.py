import asyncio
import inspect


# Note the dual concept is still to be determined... (something speeding up scheduler/eventloop somehow...)
import time
from datetime import datetime, MINYEAR, timedelta

import typing
import wrapt

from timecontrol.calllimiter import TimePeriod, TimePoint

from structlog import get_logger


def calllogger(timer: typing.Callable[[], TimePoint] = datetime.now,):
    def decorator(wrapper):
        @wrapt.decorator
        def calllogged_function(wrapped, instance, args, kwargs):
            # TODO : maybe use the log as a trace to enable autodiff ?? cf google's JAX...
            sig = inspect.signature(wrapped)
            bound_args = sig.bind(*args, **kwargs)
            log = get_logger(wrapped.__name__)  # one logger per function definition
            log = log.bind(args=bound_args.args, **bound_args.kwargs)
            res = wrapped(*bound_args.args, **bound_args.kwargs)
            log = log.bind(result=res)
            log.info(f"{wrapped.__name__} called: ")

        @wrapt.decorator
        async def async_calllogged_function(wrapped, instance, args, kwargs):

            sig = inspect.signature(wrapped)
            bound_args = sig.bind(*args, **kwargs)
            log = get_logger(wrapped.__name__)  # one logger per function definition
            log = log.bind(args=bound_args.args, **bound_args.kwargs)
            log.info(f"{wrapped.__name__} called: ")
            # TODO : som magic trick to resolve the result later (future, final log output magic ?)
            res = await wrapped(*bound_args.args, **bound_args.kwargs)
            log = log.bind(result=res)
            log.info(f"{wrapped.__name__} returned: ")

        # Note : in this decorator generators or classes are not considered...
        # it throttles only the usual call.

        # checking for async first, to avoid too much if-nesting
        if inspect.iscoroutinefunction(wrapper):
            wrap = async_calllogged_function(wrapper)

            # then the more general case
        elif inspect.isfunction(wrapper) or inspect.ismethod(wrapper):
            wrap = calllogged_function(wrapper)

            # did we forget any usecase ?
        else:
            raise NotImplementedError(f"eventful doesnt support decorating {wrapper}")

        return wrap

    return decorator


if __name__ == "__main__":

    @calllogger()
    def answer(*args, **kwargs):
        time.sleep(0.5)
        return kwargs["answer"]

    now = datetime.now()
    while datetime.now() - now < timedelta(seconds=2):
        answer("the", "answer", "is", 42, answer=42)

    @calllogger()
    async def async_answer(*args, **kwargs):
        await asyncio.sleep(0.5)
        return kwargs["async_answer"]

    async def async_runner():
        now = datetime.now()
        while datetime.now() - now < timedelta(seconds=2):
            await async_answer("the", "async", "answer", "is", 42, async_answer=42)

    asyncio.run(async_runner())
