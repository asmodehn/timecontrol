import asyncio
import inspect


# Note the dual concept is still to be determined... (something speeding up scheduler/eventloop somehow...)
import time
from datetime import datetime, MINYEAR, timedelta

import typing
import wrapt


def run(
    *maybe_coros: typing.Any, **kwargs: typing.Any
) -> typing.Tuple[
    typing.Any
]:

    result = tuple()

    # TODO : kwargs as extra arguments ? background scheduler ? ? YAGNI => we ll see...

    for c in maybe_coros:
        if inspect.iscoroutine(c):
            try:
                loop = asyncio.get_running_loop()
                result = result + (loop.run_until_complete(c),)
            except RuntimeError as re:
                # we currently have no running loop:
                result = result + (asyncio.run(c),)
        else:
            result = result + (c,)

    return None if not result else result[0] if len(result) == 1 else result
    # returning a tuple (attempting to get inverse semantics to args)

    # TODO : include scheduler work to trigger decorated pydefs


if __name__ == "__main__":

    def printer(*args, **kwargs):
        print(f"{datetime.now()} : {args}, {kwargs}")
        return 42

    # doesnt disturb usual call
    r = printer("the", "answer", "is", 42, answer=42)
    assert r == 42

    async def async_printer(*args, **kwargs):
        print(f"{datetime.now()} : {args}, {kwargs}")
        return 42

    # lazy run via async coroutines
    assert run() == None  # computes nothing, does nothing

    # run it via run continuations => explicit execution sequence
    res = run(async_printer())
    assert res == 42
