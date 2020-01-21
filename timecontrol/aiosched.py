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
import time
import heapq
from collections import namedtuple
import threading
from time import monotonic as _time

from sched import Event, scheduler

#class Event(namedtuple('Event', 'time, priority, action, argument, kwargs')):

_sentinel = object()


class aioscheduler(scheduler):

    def __init__(self, timefunc=_time, delayfunc=asyncio.sleep):
        """Initialize a new instance, passing the time and delay
        functions"""
        super(aioscheduler, self).__init__(timefunc=timefunc, delayfunc=delayfunc)

    async def run(self, blocking=True):
        """Execute events until the queue is empty.
        If blocking is False executes the scheduled events due to
        expire soonest (if any) and then return the deadline of the
        next scheduled call in the scheduler.

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

        A questionable hack is added to allow other threads to run:
        just after an event is executed, a delay of 0 is executed, to
        avoid monopolizing the CPU when other threads are also
        runnable.

        """
        # localize variable access to minimize overhead
        # and to improve thread safety
        lock = self._lock
        q = self._queue
        delayfunc = self.delayfunc
        timefunc = self.timefunc
        pop = heapq.heappop
        while True:
            with lock:
                if not q:
                    break
                time, priority, action, argument, kwargs = q[0]
                now = timefunc()
                if time > now:
                    delay = True
                else:
                    delay = False
                    pop(q)
            if delay:
                if not blocking:
                    return time - now
                await delayfunc(time - now)
            else:
                action(*argument, **kwargs)
                await delayfunc(0)   # Let other threads run


if __name__ == '__main__':


    s = aioscheduler(time.time, asyncio.sleep)

    def print_time(a='default'):
         print("From print_time", time.time(), a)

    async def print_some_times():
         print(time.time())
         s.enter(10, 1, print_time)
         s.enter(5, 2, print_time, argument=('positional',))
         s.enter(5, 1, print_time, kwargs={'a': 'keyword'})
         await s.run()
         print(time.time())

    asyncio.run(print_some_times())  # The schedule
    # 930343690.257
    # From print_time 930343695.274 positional
    # From print_time 930343695.275 keyword
    # From print_time 930343700.273 default
    # 930343700.276
