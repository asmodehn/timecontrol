import time


class UnderTimeLimit(Exception):
    def __init__(self, message, elapsed, expected):
        self.elapsed = elapsed
        self.expected = expected
        super(UnderTimeLimit, self).__init__(message)


class UnderLimiter:
    """
    A way to throttle successive calls.
    Note : To make any sense at all, this has to be a strict requirement. otherwise it s just a normal 'asap' call.
    """

    def __init__(self, period, timer=time.time):
        self.timer = timer
        self.period = period
        self._last = self.timer()
        # Setting last as now, to prevent accidental bursts on creation.

    def __call__(self, fun = None):
        """Decorator"""

        def wrapper(*args, **kwargs):

            # Measure time
            now = self.timer()
            if now - self._last < self.period:
                # Raise Limit exception if too fast.
                raise UnderTimeLimit("Under Time Limit", elapsed=now-self._last, expected=self.period)
            else:
                if fun:
                    self._last = now
                    return fun(*args, **kwargs)
                # else Noop -> returns None
        return wrapper
