import inspect
import time

import typing

import wrapt
import asyncio
from asyncio import AbstractEventLoop, Task


# TODO : properly type all these decorators to make mypy happy (need hints for wrapt first)

AgentTask = typing.Callable[[AbstractEventLoop], Task]


_T = typing.TypeVar("_T")


@wrapt.decorator
def fun2coro(wrapped: typing.Callable[..., _T], instance, args, kwargs) -> typing.Coroutine[typing.Any, typing.Any, _T]:
    """ Simplest decorator to reliably turn a function into a coroutine.
    This makes it doable from the call site (instead of having to redefine it with async def)
    """

    async def fun_wrapper(*args, **kwargs) -> _T:
        return wrapped(*args, **kwargs)

    # if coroutine we can forward the call already.
    if inspect.iscoroutinefunction(wrapped) or inspect.isasyncgenfunction(wrapped):
        return wrapped(*args, **kwargs)

    return fun_wrapper(*args, **kwargs)


def delayed(delay: float=0.0, sleeper: typing.Callable=asyncio.sleep):
    @wrapt.decorator
    def decorator(wrapped: typing.Callable[..., _T], instance, args, kwargs) -> typing.Coroutine[typing.Any, typing.Any, _T]:
        """ Simplest decorator to reliably delay a coroutine execution by a relative amount of time.
        This makes it doable from the call site (instead of having to add delay in the definition).
        It is also usable for a normal function, if a sleeper method is passed as argument.
        """
        nonlocal sleeper

        async def delayed_async_wrapper(*args, **kwargs):
            await sleeper(delay=delay)
            if inspect.isasyncgenfunction(wrapped):  # a kind of special thing...
                return wrapped(*args, **kwargs)
            else:
                return await wrapped(*args, **kwargs)

        def delayed_wrapper(*args, **kwargs):
            sleeper(delay=delay)
            return wrapped(*args, **kwargs)

        # if coroutine or asyncgen.
        if inspect.iscoroutinefunction(wrapped) or inspect.isasyncgenfunction(wrapped):
            # asserting the sleep is of same nature as the wrapped callable
            # TODO : test this properly the sleeper to be async (async function OR async method)
            # TODO : with types ?
            return delayed_async_wrapper(*args, **kwargs)
        else:
            # asserting the sleep is of same nature as the wrapped callable
            assert inspect.isfunction(sleeper) or inspect.ismethod(sleeper)  # TODO : test this properly with types ?
            return delayed_wrapper(*args, **kwargs)

    return decorator


# TODO : throttle, to sleep in between generator loop (before yielding)
#  Behavior could be to fallback on delay for functions and coroutines...


# TODO : maybe this one is not useful after all...
def background(loop: AbstractEventLoop):
    @wrapt.decorator
    def decorator(wrapped: typing.Callable[..., _T], instance, args, kwargs) -> typing.Coroutine[typing.Any, typing.Any, _T]:
        """ Simplest decorator to reliably schedule a coroutine to run as a task of the loop
        This makes it doable between the call site and the definition, when the loop is not accessible in other places.
        BEWARE of infinite loops without sleeps !
        """

        async def trampoline_wrapper(*args, **kwargs):
            return loop.create_task(wrapped(*args, **kwargs))

        return trampoline_wrapper(*args, **kwargs)

    return decorator


# TODO : isnt this similar to a inifinite (async?) generator ?
def trampoline(loop: AbstractEventLoop):
    @wrapt.decorator
    def decorator(wrapped: typing.Callable[..., _T], instance, args, kwargs) -> typing.Coroutine[typing.Any, typing.Any, _T]:
        """ Simplest decorator to reliably trampoline a coroutine.
        This makes it doable from the callsite (instead of having to add trampoline in the definition).
        BEWARE of infinite background loops without sleeps !
        """

        async def trampoline_wrapper(*args, **kwargs):
            res = await wrapped(*args, **kwargs)  # First result to init
            loop.create_task(wrapped(*args, **kwargs))  # then background...
            return res

        return trampoline_wrapper(*args, **kwargs)

    return decorator


def traced(log: typing.Dict[float, _T]):
    @wrapt.decorator
    def decorator(wrapped: typing.Callable[..., _T], instance, args, kwargs) -> typing.Coroutine[typing.Any, typing.Any, _T]:
        """ Simplest decorator to reliably add a trace to a coroutine.
        This makes it doable from the callsite (instead of having to add a trace in the definition).
        """

        async def traced_wrapper(*args, **kwargs):
            sig = inspect.signature(wrapped)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            log[bound_args] = await wrapped(*bound_args.args, **bound_args.kwargs)
            return log[bound_args]

        return traced_wrapper(*args, **kwargs)

    return decorator


def agenttask(delay=0.1, trampoline=False, sleeper=asyncio.sleep):
    """
    A decorator to delay the task creation until an eventloop is passed as argument.
    This will also wrap functions inside coroutines, to be executed only as part of an eventloop.
    :param args:
    :param kwargs:
    :return:
    """

    def decorator(wrapped):
        @wrapt.decorator
        def coro2task(wrapped, instance, args, kwargs) -> AgentTask:

            # add a delay if needed *after* the call (to ensure a coro), but *before* the schedule.
            if delay:
                wrapped = delayed(delay, sleeper=sleeper)(wrapped)

            if trampoline:
                wrapped = trampoline(wrapped)

            def trampoline_with_loop(loop: AbstractEventLoop) -> Task:

                async def trampoline_wrapper(*args, **kwargs) -> Task:
                    res = await wrapped(*args, **kwargs)
                    loop.create_task(trampoline_wrapper(*args, **kwargs))
                    return res

                # return a task to be executed soon
                return loop.create_task(wrapped(*args, **kwargs))

            def with_loop(loop: AbstractEventLoop) -> Task:
                # return a task to be executed soon
                return loop.create_task(wrapped(*args, **kwargs))

            return with_loop

        # checking for async first, to avoid too much if-nesting
        if inspect.iscoroutinefunction(wrapped):
            wrap = coro2task(wrapped)

        # TODO : we need to schedule calls here.
        #  But for methods, we need to wait for class instantiation...
        # then the more general case
        elif inspect.isfunction(wrapped) or inspect.ismethod(wrapped):
            wrap = coro2task(fun2coro(wrapped))  # no change at all

            # did we forget any usecase ?
        else:
            raise NotImplementedError(
                f"agentloop.at doesnt support decorating {wrapped}"
            )

        return wrap  # as a normal decorator would

    return decorator


if __name__ == "__main__":

    @agenttask()
    def myfun():
        print("running myfun")
        return 42

    @agenttask()
    async def mycoro():
        print("running mycoro")
        return 42

    @agenttask(delay=1.5)
    async def mydelayedcoro():
        print("running mydelayedcoro")
        return 42

    loop = asyncio.get_event_loop()

    tfun = myfun()
    print(tfun)

    tcoro = mycoro()
    print(tcoro)

    tdelayedcoro = mydelayedcoro()
    print(tdelayedcoro)

    aiotfun = tfun(loop)  # scheduled
    print(f"{tfun} scheduled as {aiotfun}")

    aiotcoro = tcoro(loop)  # scheduled
    print(f"{tcoro} scheduled as {aiotcoro}")

    aiotdelayedcoro = tdelayedcoro(loop)  # scheduled
    print(f"{tdelayedcoro} scheduled as {aiotdelayedcoro}")

    time.sleep(1)
    print("starting loop")
    loop.run_until_complete(
        asyncio.sleep(5)
    )  # need enough time to run everything, or it will just not happen.