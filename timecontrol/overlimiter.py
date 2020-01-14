import asyncio
import inspect
import time


class OverTimeLimit(Exception):
    def __init__(self, message, result, elapsed, expected):
        self.result = result
        self.elapsed = elapsed
        self.expected = expected
        super(OverTimeLimit, self).__init__(message)


class OverLimiter:
    """
    A way to trigger successive calls
    Note : To make any sense at all, this has to be a lax requirement. otherwise we can never correct...
    """

    def __init__(self, period, timer=time.time):
        self.timer = timer
        self.period = period
        self._last = 0
        # Setting last as long time ago, to force speedup on creation.

    def __call__(self, fun=None):
        """Decorator"""

        def wrapper(*args, **kwargs):

            # Measure time
            now = self.timer()

            if fun:
                # call function anyway (lax requirement)
                result = fun(*args, **kwargs)

                if now - self._last > self.period:

                    # Raise Limit exception if too slow.
                    ret = OverTimeLimit(
                        "Over Time Limit", result=result, elapsed=now - self._last, expected=self.period
                    )
                else:
                    # need to do that after the > period check !
                    self._last = now

                    ret = result

                # need to do that after the > period check ! and the exception creation
                self._last = now

                # TODO : C++ Result design ( cf category theory, etc.) TODO : find reference...
                if isinstance(ret, Exception):
                    raise ret
                else:
                    return ret

            # else Noop -> returns None

        async def async_wrapper(*args, **kwargs):

            # Measure time
            now = self.timer()

            if fun:
                # call function anyway (lax requirement)
                result = await fun(*args, **kwargs)

                if now - self._last > self.period:

                    # Raise Limit exception if too slow.
                    ret = OverTimeLimit(
                        "Over Time Limit", result=result, elapsed=now - self._last, expected=self.period
                    )
                else:
                    # need to do that after the > period check !
                    self._last = now

                    ret = result

                # need to do that after the > period check ! and the exception creation
                self._last = now

                # TODO : C++ Result design ( cf category theory, etc.) TODO : find reference...
                if isinstance(ret, Exception):
                    raise ret
                else:
                    return ret

            # else Noop -> returns None

        # we need to propagate the nature of fun to avoid troubles in other places...
        if asyncio.iscoroutinefunction(fun):
            return async_wrapper
        else:
            return wrapper
