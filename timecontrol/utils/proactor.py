# decorator with a simple design
# Function => Generator
# Corountine => AsyncGen
# Generator => Generator
# AsyncGen => AsyncGen

# this provides an interface to specify the driver (a stream to be filled...)
# This is similar to generators leveraging the "send" interface...
import inspect
from typing import AsyncGenerator, Callable, Generator, Iterable, Iterator, Union

import wrapt


# TODO : a trigger_from_iterable function ? similar to hypothesis strategy for the dev interface...

# TODO : this could be a good place to plug aiostreams as param triggers (we only need iterator interface after all)...

def proactor(*, trigger: Union[Iterator, Generator, AsyncGenerator] = None):

    @wrapt.decorator
    def wrapper_function(wrapped, instance, args, kwargs):
        nonlocal trigger
        for yld in trigger:
            # TODO : maybe this check can be done previouslyto have 2 simpler wrappers...
            if inspect.isgeneratorfunction(wrapped):  # if this is a generator, we want to extract all
                yield [v for v in wrapped(*args, **kwargs, proactor_triggered=yld)]
            else:
                yield wrapped(*args, **kwargs, proactor_triggered=yld)

    @wrapt.decorator
    async def wrapper_async_function(wrapped, instance, args, kwargs):
        nonlocal trigger
        async for yld in trigger:  # TODO : maybe the async should be somehow delegated here ? (from trigger as param to decorator...)
            if inspect.isgeneratorfunction(wrapped):  # if this is a generator, we want to extract all
                yield [v for v in wrapped(*args, **kwargs, proactor_triggered=yld)]
            else:
                yield wrapped(*args, **kwargs, proactor_triggered=yld)

    @wrapt.decorator
    async def wrapper_function_async(wrapped, instance, args, kwargs):
        nonlocal trigger
        for yld in trigger:
            if inspect.isasyncgenfunction(wrapped):  # if this is a generator, we want to extract all
                yield [v async for v in wrapped(*args, **kwargs, proactor_triggered=yld)]
            else:
                yield await wrapped(*args, **kwargs, proactor_triggered=yld)

    @wrapt.decorator
    async def wrapper_async_function_async(wrapped, instance, args, kwargs):
        nonlocal trigger
        async for yld in trigger:
            if inspect.isasyncgenfunction(wrapped):  # if this is a generator, we want to extract all
                yield [v async for v in wrapped(*args, **kwargs, proactor_triggered=yld)]
            else:
                yield await wrapped(*args, **kwargs, proactor_triggered=yld)

    def decorator(func):

        if inspect.isasyncgenfunction(func):
            if inspect.isasyncgen(trigger):
                return wrapper_async_function_async(func) ()  # starting generator immediately
            else:  # default to simpler usecase
                return wrapper_function_async(func) ()  # starting generator immediately

        elif inspect.iscoroutinefunction(func):
            if inspect.isasyncgen(trigger):
                return wrapper_async_function_async(func) () # starting generator immediately
            else:  # default to simpler usecase
                return wrapper_function_async(func) () # starting generator immediately

        elif inspect.isfunction(func) or inspect.ismethod(func):
            if inspect.isasyncgen(trigger):
                return wrapper_async_function(func) ()  # starting generator immediately
            else:  # default to simpler usecase
                return wrapper_function(func) ()  # starting generator immediately
        else:
            raise RuntimeError(f"proactor decorator is not usable with {func}")

    return decorator


if __name__ == '__main__':
    import asyncio
    from datetime import datetime

    @proactor(trigger=iter([1, 2, 3]))
    def printer(**kwargs):
        print(f"{kwargs}: {datetime.now()}")
        return kwargs

    # direct
    for p in printer:
        print(p)

    @proactor(trigger=iter([1, 2, 3]))
    async def printer(**kwargs):
        await asyncio.sleep(0.1)
        print(f"{kwargs}: {datetime.now()}")
        return kwargs

    # direct coroutine
    for p in asyncio.run(printer):
        print(p)


