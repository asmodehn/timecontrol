"""A generally useful event scheduler class, asyncio version.

Each instance of this class manages its own queue.
No multi-threading is implied, however asynchronous scheduling is supported,
meaning that multiple scheduler in one event loop will synchronise things in the same event loop.

Each instance is parametrized with two functions, one that is
supposed to return the current time, one that is supposed to
implement a delay. Both of these can be asynchronous

Events are usual python's schedule events. see sched.py for reference.
"""
import asyncio
import inspect
import time
import heapq
from collections import namedtuple
import threading
from time import monotonic as _time

from sched import scheduler


class aioscheduler(scheduler):

    def __init__(self, timefunc=_time, delayfunc=asyncio.sleep, loop=None):
        """Initialize a new instance, passing the time and delay
        functions"""
        self.loop = asyncio.get_event_loop() if loop is None else loop
        super(aioscheduler, self).__init__(timefunc=timefunc, delayfunc=delayfunc)

    async def run(self, blocking=False):
        """Execute events until the queue is empty.
        If blocking is True, keeps control via a while loop, just like the sync scheduler.
        By default it is non-blocking, returning as soon as waiting or call has been done.

        When there is a positive delay until the first event, the
        delay function is called and the event is left in the queue;
        otherwise, the event is removed from the queue and executed
        (its action function is called, passing it the argument).  If
        the delay function returns prematurely, it is simply
        restarted.

        It is legal for both the delay function and the action
        function to modify the queue or to raise an exception;
        exceptions are not caught but the scheduler's state remains
        well-defined so run() may be called again.

        """
        # localize variable access to minimize overhead
        # and to improve thread safety
        lock = self._lock
        q = self._queue
        delayfunc = self.delayfunc
        timefunc = self.timefunc
        pop = heapq.heappop

        # TODO : keep track of reentrant calls...

        while q:
            with lock:
                time, priority, action, argument, kwargs = q[0]
                now = timefunc()
                if time > now:
                    delay = True
                else:
                    delay = False
                    pop(q)
            if delay:
                if not blocking:
                    self.loop.create_task(self.run(True))
                    # background blocking loop to still execute the action later
                    return time - now
                else:
                    await delayfunc(time - now)
            elif callable(action):
                # Note : we are outside of control flow:
                #  Result cannot be returned, it must be retrieved from some log.
                if inspect.iscoroutinefunction(action):
                    await action(*argument, **kwargs)
                else:
                    action(*argument, **kwargs)


if __name__ == '__main__':

    # create loop
    l = asyncio.get_event_loop()

    s = aioscheduler(loop=l, timefunc=time.time, delayfunc=asyncio.sleep)

    async def print_time(a='default'):
         await asyncio.sleep(1)
         print("From print_time", time.time(), a)

    async def print_some_times():
         print(f"Start planning {time.time()}")
         s.enter(10, 1, print_time)
         s.enter(5, 2, print_time, argument=('positional',))
         s.enter(5, 1, print_time, kwargs={'a': 'keyword'})
         await s.run()
         print(f"End planning {time.time()}")

    l.create_task(print_some_times())
    # The schedule

    l.run_forever()
    # 930343690.257
    # From print_time 930343695.274 positional
    # From print_time 930343695.275 keyword
    # From print_time 930343700.273 default
    # 930343700.276
