import inspect
import time

import typing
import wrapt
import asyncio
from asyncio import AbstractEventLoop, Task


# TODO : properly type all these decorators to make mypy happy (need hints for wrapt first)

AgentTask = typing.Callable[[AbstractEventLoop], Task]


@wrapt.decorator
def fun2coro(wrapped, instance, args, kwargs):
    """ Simplest decorator to reliably turn a function into a coroutine.
    This makes it doable from the call site (instead of having to redefine it with async def)
    """

    async def fun_wrapper(*args, **kwargs):
        return wrapped(*args, **kwargs)

    return fun_wrapper(*args, **kwargs)


def delayed(delay=0, sleeper=asyncio.sleep):
    @wrapt.decorator
    def decorator(wrapped, instance, args, kwargs):
        """ Simplest decorator to reliably delay a coroutine execution by a relative amount of time.
        This makes it doable from the call site (instead of having to add delay in the definition
        """

        async def delayed_wrapper(*args, **kwargs):
            await sleeper(delay=delay)
            return await wrapped(*args, **kwargs)

        return delayed_wrapper(*args, **kwargs)

    return decorator


def agenttask(delay=0, sleeper=asyncio.sleep):
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
