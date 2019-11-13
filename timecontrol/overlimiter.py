import time

from timecontrol.underlimiter import UnderTimeLimit


class OverLimiter:
    """
    A way to throttle successive calls
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
            if now - self._last > self.period:
                # Raise Limit exception if too slow.
                raise OverTimeLimit("Over Time Limit", elapsed=now-self._last, expected=self.period)
            else:
                if fun:
                    return fun(*args, **kwargs)
                # else Noop -> returns None
        return wrapper


class OverTimeLimit(Exception):
    def __init__(self, message, elapsed, expected):
        self.elapsed = elapsed
        self.expected = expected
        super(OverTimeLimit, self).__init__(message)