# decorator with a simple design:
# Function => Generator  TODO : should be Function, aggregation might be a different decorator
# Corountine => AsyncGen  TODO : should be Coroutine, aggregation might be a different decorator
# Generator => Generator
# AsyncGen => AsyncGen

# TODO:
# Function => Function
# Corountine => Coroutine
# Generator => Function  TODO : should be Generator. Gen -> Func might be a different decorator
# AsyncGen => Coroutine  TODO: should be AsyncGEn. AsyncGen -> Coro might be a different decorator

# This just reacts to calls and return a result.
# This is similar to a generator just yielding a list of values from arguments
import inspect
from typing import AsyncGenerator, Callable, Generator, Iterator, MutableSequence, Union

import wrapt


def reactor(*, effector: Union[Callable, Generator, AsyncGenerator] = None):  # None means no output, so nothing happens...

    @wrapt.decorator
    def wrapper_function(wrapped, instance, args, kwargs):
        res = wrapped(*args, **kwargs)
        if inspect.isgenerator(effector):
            effector.send(res)  # pass it to the effector, but effector behavior doesnt affect the reactor.
        elif callable(effector):  # assumed simple callable (imperative python !)
            effector(res)
        return res  # because we dont want to modify a decorated pydef behavior...

    @wrapt.decorator
    async def wrapper_function_async(wrapped, instance, args, kwargs):
        res = await wrapped(*args, **kwargs)
        if inspect.isgenerator(effector):
            effector.send(res)
        elif callable(effector):  # assumed simple callable (imperative python !)
            effector(await wrapped(*args, **kwargs))
        elif effector is not None:
            effector
        return res  # because we dont want to modify a decorated pydef behavior...

    @wrapt.decorator
    def wrapper_generator(wrapped, instance, args, kwargs):
        for yld in wrapped(*args, **kwargs):
            # if inspect.isasyncgen(effector):  TODO : what about asyncgen in this case ??
            #     await effector.asend(yld)
            # elif
            if inspect.isgenerator(effector):
                effector.send(yld)  # use generator communication
            elif callable(effector):  # assumed simple callable (imperative python !)
                effector(yld)  # use function communication
            elif effector is not None:
                effector
            yield yld


    @wrapt.decorator
    async def wrapper_generator_async(wrapped, instance, args, kwargs):
        async for yld in wrapped(*args, **kwargs):
            if inspect.isasyncgen(effector):
                await effector.asend(yld)
            elif inspect.isgenerator(effector):
                effector.send(yld)
            elif callable(effector):  # assumed simple callable (imperative python !)
                effector(yld)
            elif effector is not None:
                effector
            yield yld

    def decorator(func):

        if inspect.isgenerator(effector):
            # initializing generator
            effector.send(None)

        if inspect.isasyncgenfunction(func):
            return wrapper_generator_async(func)

        elif inspect.iscoroutinefunction(func):
            return wrapper_function_async(func)

        elif inspect.isgeneratorfunction(func):
            return wrapper_generator(func)

        elif inspect.isfunction(func) or inspect.ismethod(func):
            return wrapper_function(func)

        else:
            raise RuntimeError(f"reactor decorator is not usable with {func}")

    return decorator


if __name__ == '__main__':
    import asyncio
    from datetime import datetime

    @reactor(effector=lambda x: print(f"eff: {x}"))
    def printer(**kwargs):
        yield datetime.now()
        yield kwargs

    # direct
    for _ in printer(arg="myargs"):
        pass  # effector will do its thing

    @reactor(effector=lambda x: print(f"eff: {x}"))
    async def printer(**kwargs):
        await asyncio.sleep(0.1)
        yield datetime.now()
        yield kwargs

    async def arun():
        async for _ in printer(arg="myargs"):
            pass  # effector will do its thing...

    # direct coroutine
    asyncio.run(arun())
