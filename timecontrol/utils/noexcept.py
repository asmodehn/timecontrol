import inspect
from typing import Callable

import wrapt
from result import Err, Ok, Result

# TODO: noexcept(noexcept(f)) -> noexcept(f)


def noexcept(func):
    """
    A simple decorator preventing side-effect as much as reasonably possible.
    The aim is to allow practical "async runs in the background" without losing usual python behavior.
    :param func:
    :return:
    """

    if inspect.isasyncgenfunction(func):
        # @functools.wraps(func)
        # async def pure_wrapper(*args, **kwargs):
        @wrapt.decorator
        async def pure_wrapper(wrapped, instance, args, kwargs):
            """ wrapping an async generator into a safe async function, returning a stream of result"""
            try:
                async for yld in wrapped(*args, **kwargs):
                    if not isinstance(yld, Result):
                        yield Ok(yld)
                    else:
                        yield yld
            except Exception as e:
                yield Err(e)  # any error stops the generator
            finally:  # TODO : check for run usecase not covered ??
                pass  # nothing specific to return here

        return pure_wrapper(func)

    elif inspect.isgeneratorfunction(func):

        # @functools.wraps(func)
        # def pure_wrapper(*args, **kwargs):
        @wrapt.decorator
        def pure_wrapper(wrapped, instance, args, kwargs):
            """wrapping a generator into a safe generator"""
            try:
                for yld in wrapped(*args, **kwargs):
                    if not isinstance(yld, Result):
                        yield Ok(yld)
                    else:
                        yield yld
            except Exception as e:
                yield Err(e)  # any error stops the generator
            finally:  # TODO : check for run usecase not covered ??
                pass  # nothing specific to return here

        return pure_wrapper(func)

    elif inspect.iscoroutinefunction(func):

        # @functools.wraps(func)
        # async def pure_wrapper(*args, **kwargs):
        @wrapt.decorator
        async def pure_wrapper(wrapped, instance, args, kwargs):
            try:
                res = await wrapped(*args, **kwargs)
                if not isinstance(res, Result):
                    res = Ok(res)
            except Exception as e:
                res = Err(e)
            finally:  # TODO : check for run usecase not covered ??
                return res

        return pure_wrapper(func)

    elif inspect.isfunction(func) or inspect.ismethod(func):

        # @functools.wraps(func)
        # def pure_wrapper(*args, **kwargs):
        @wrapt.decorator
        def pure_wrapper(wrapped, instance, args, kwargs):
            try:
                res = wrapped(*args, **kwargs)
                if not isinstance(res, Result):
                    res = Ok(res)
            except Exception as e:
                res = Err(e)
            finally:  # TODO : check for run usecase not covered ??
                return res

        return pure_wrapper(func)

    # TODO : generators & asyncgens !!
    else:
        raise NotImplementedError(f"noexcept doesnt support decorating {func}")


if __name__ == '__main__':

    @noexcept
    def usual_result():
        return 42

    @noexcept
    def exceptional_result():
        raise RuntimeError("Exceptional result")

    print(usual_result().ok())
    print(exceptional_result().err())

    # possible reraise
    raise exceptional_result().err()




