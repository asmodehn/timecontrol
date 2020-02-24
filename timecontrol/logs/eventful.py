import inspect
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta, MINYEAR
import typing
from result import Result

# TODO : different kinds of !structured! log / dataframes, etc.
from timecontrol.underlimiter import UnderTimeLimit
from timecontrol.overlimiter import OverTimeLimit


@dataclass(frozen=True, init=False)
class CommandCalled:
    # TODO : more time representation
    timestamp: typing.Union[int, datetime]
    bound_args: typing.FrozenSet  # we need a frozenset here to be hashable

    def __init__(self, bound_arguments: inspect.BoundArguments, timestamp: typing.Union[int, datetime] = None):
        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)
        object.__setattr__(self, "timestamp", timestamp)
        # we change bound arguments to a frozenset (to be hashable)
        object.__setattr__(self, "bound_args", frozenset(bound_arguments.arguments.items()))
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


CommandEvent = typing.Union[CommandCalled, CommandReturned]


class EventfulDef:
    """
    An EventfulDef.
    This wraps a python routine definition into a generator, generating events

    >>> def inc(a: int):
    ...    return a+1
    >>> einc = EventfulDef(inc)

    >>> print(einc)  # doctest: +ELLIPSIS
    <__main__.EventfulDef object at 0x...>
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

    >>> einc = EventfulDef(inc)

    >>> print(einc)  # doctest: +ELLIPSIS
    <__main__.EventfulDef object at 0x...>
    >>> for e in einc(41):
    ...    print(e)  # doctest: +ELLIPSIS
    CommandCalled(timestamp=datetime.datetime(...), bound_args=frozenset({('a', 41)}))
    CommandReturned(timestamp=datetime.datetime(...), result=Ok(42))
    CommandReturned(timestamp=datetime.datetime(...), result=Ok(43))
    CommandReturned(timestamp=datetime.datetime(...), result=Ok(44))

    Note : attempting to split the call/return couple seems to lead to a different, more functional,
     more elementary/low-level design, which doesn't seem to be a good fit for python.
    It is not suitable in our case, especially since this aims to be used as often as possible...
    Therefore we accumulated a bunch of code in here, also with code related to time and synchronization.
    """

    def __init__(self, cmd,
                 period_min: typing.Optional[timedelta] = None,
                 period_max: typing.Optional[timedelta] = None,
                 timer: typing.Callable[[], datetime] = datetime.now):
        self.cmd = cmd
        self._sig = inspect.signature(self.cmd)
        self.timer = timer

        self.period_min = period_min
        self.period_max = period_max

        self._last = self.timer()
        # Setting last as now, to prevent accidental bursts on creation.

        self._inner_last = datetime(year=MINYEAR, month=1, day=1)
        # Setting last as long time ago, to force speedup on creation.

    def __call__(self, *args, **kwargs):

        # checking arguments binding early
        bound_args = self._sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        if self.period_min:
            # Measure time
            now = self.timer()

            # sleep if needed (this can be addressed locally)
            if now - self._last < self.period_min:
                # Call too fast.
                # sleeps expected time period - already elapsed time
                time.sleep((self.period_min - (now - self._last)).seconds)
            else:
                self._last = now

        yield CommandCalled(timestamp=self.timer(), bound_arguments=bound_args)

        try:
            res = self.cmd(*bound_args.args, **bound_args.kwargs)

            # local closure to avoid code duplication here
            def result_event(e) -> CommandReturned:
                # Measure time
                inner_now = self.timer()

                result = Result.Ok(e)
                if self.period_max and inner_now - self._inner_last > self.period_max:
                    # Call too slow
                    # Log exception (we cannot do anything locally - it is up to the scheduler who scheduled us)
                    ret = CommandReturnedLate(result=result, timestamp_bound=self._inner_last + self.period_max, timestamp=self.timer())
                else:
                    ret = CommandReturned(result=result, timestamp=self.timer())

                # need to do that after the > period check !
                self._inner_last = inner_now

                return ret

            if inspect.isgenerator(res):
                # Note this execution flow is linear (one or more result).
                for e in res:
                    # Note: the loop being at this level, shows that this generator
                    # should not access resources "out of system border".
                    # In this case everything is supposedly "internal" (ie in python interpreter process).
                    yield result_event(e)
                    # Note: this internally can return result with a "late" result type.
                    # This is a signal for an external system to do something (nothing can be done in here)
            else:
                # Note this execution flow is affine (zero or at most one result) but with python exception handling,
                #  we attempt make it exactly one (useful to get determinism for "in-system" usecases)
                yield result_event(res)
            return
        except Exception as exc:
            result = Result.Err(exc)
            yield CommandReturned(result=result, timestamp=self.timer())
            raise  # to propagate any unexpected exception (the usual expected behavior)


class AsyncEventfulDef:
    """
    The async version of An Eventful Gen Def.
    This wraps a python async definition in another async generator, timing values yielded.
    >>> import asyncio
    >>> async def inc(a: int):
    ...     await asyncio.sleep(1)
    ...     return a+1

    >>> ainc = AsyncEventfulDef(inc)

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

    >>> ainc = AsyncEventfulDef(inc)

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


    Note : attempting to merge this with other EventfulDef leads to a different, more functional,
     more elementary/low-level) design, which doesn't seem to be a good fit for python.
    It is not suitable in our case, especially since this aims to be used as often as possible...
    Therefore we duplicated the code around.

    """

    def __init__(self, cmd, timer: typing.Callable[[], datetime] = datetime.now):
        self.cmd = cmd
        self._sig = inspect.signature(self.cmd)
        self.timer = timer

    async def __call__(self, *args, **kwargs):
        # checking arguments binding early
        bound_args = self._sig.bind(*args, **kwargs)
        bound_args.apply_defaults()

        yield CommandCalled(timestamp=self.timer(), bound_arguments=bound_args)

        # Note this execution flow is affine (zero or at most one result) but with python exception handling,
        #  we attempt make it exactly one result (useful to get determinism for "in-system" usecases)
        try:

            res = self.cmd(*bound_args.args, **bound_args.kwargs)
            try:
                if inspect.isasyncgen(res):
                    async for e in res:
                        # Note : this being an async generator, we are expected to "wait some time" between each call.
                        # We will interract with "out of system" processes,
                        #  and can expect few things (provided they match python interpreter's capabilities...)
                        result = Result.Ok(e)
                        yield CommandReturned(result=result, timestamp=self.timer())
                    # This should be in a 'finally' clause, if we could get rid of undertimelimit case
                    return
                else:
                    result = Result.Ok(await res)
                    yield CommandReturned(result=result, timestamp=self.timer())
                    # This should be in a 'finally' clause, if we could get rid of undertimelimit case
                    return
            except UnderTimeLimit as utl:
                # TODO : this maybe a sign we need a different design for underlimit
                #  so that log doesnt have to be aware of it...
                raise  # raise without logging

        except OverTimeLimit as utl:
            # TODO : this maybe a sign we need a different design for underlimit
            #  so that log doesnt have to be aware of it...
            raise  # raise without logging
        except Exception as exc:
            result = Result.Err(exc)
            yield CommandReturned(result=result, timestamp=self.timer())
            # This should be in a 'finally' clause, if we could get rid of undertimelimit case
            raise  # to propagate any unexpected exception (the usual expected behavior)


def eventful(timer: typing.Callable[[], datetime] = datetime.now):
    # Note :
    #  - pydef command -> event generator
    #  - async pydef command -> async event generator
    #  - generator -> event generator
    #  - async generator -> async event generator
    def decorator(cmd):

        if inspect.isfunction(cmd):
            wrapped = EventfulDef(cmd=cmd, timer=timer)
        elif inspect.iscoroutine(cmd):
            wrapped = AsyncEventfulDef(cmd=cmd, timer=timer)
        else:
            raise NotImplementedError
        return wrapped

    return decorator


if __name__ == '__main__':
    import doctest
    doctest.testmod()



