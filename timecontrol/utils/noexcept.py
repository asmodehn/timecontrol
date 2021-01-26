import inspect

import wrapt
from result import Err, Ok, Result


def noexcept(func):
    """
    A simple decorator preventing side-effect as much as reasonably possible.
    The aim is to allow practical "async runs in the background" without losing usual python behavior.
    :param func:
    :return:
    """
    if inspect.iscoroutinefunction(func):

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

    elif inspect.isfunction(func):

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




