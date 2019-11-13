import time


class OverTimeLimit(Exception):
    def __init__(self, message, elapsed, expected):
        self.elapsed = elapsed
        self.expected = expected
        super(OverTimeLimit, self).__init__(message)


class OverLimiter:
    """
    A way to trigger successive calls
    Note : To make any sense at all, this has to be a lax requirement. otherwise it s just a normal 'asap' call.
    """

    def __init__(self, period, timer=time.time):
        self.timer = timer
        self.period = period
        self._last = 0
        # Setting last as long time ago, to prevent accidental delays on creation.

    def __call__(self, fun = None):
        """Decorator"""

        def wrapper(*args, **kwargs):

            # Measure time
            now = self.timer()

            if fun:
                res = fun(*args, **kwargs)
            else:
                res = None  # else Noop -> returns None
            # TODO :  deal with return problem... (except cannot simply not return...)

            otl = None
            if now - self._last > self.period:
                # Raise Limit exception if too slow.
                otl = OverTimeLimit("Over Time Limit", elapsed=now-self._last, expected=self.period)

            self._last = now
            if otl:
                raise otl
            else:
                return res

        return wrapper

