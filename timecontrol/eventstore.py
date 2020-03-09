"""
Implementing a bounded data structure to store events (data in time)

base data model from datafun design : set, bags (counter), tuple
"""
import inspect
import queue
import random
# using asyncio queue, because of assumption of running single threaded and ability to get size.
# Note : if performance is your thing, lets reimplement this in CPython :-p
import sys
import time
import asyncio

import typing
from collections import Counter, OrderedDict, deque

# TODO EVentStore is the "append-only" store for events. needs to be coupled with eventflow to get a useful interface.
# various external interfaces can be provided
from dataclasses import dataclass
from datetime import datetime

from timecontrol.datetimeinterval import DateTimeInterval
from timecontrol.eventcounter import EventCounter, Event
from timecontrol.timeinterval import TimeInterval
from timecontrol.timelog import TimeLog


class EventStore:
    """
     A directed container / bimonad (see Danel Ahman paper) to hold event in a immutable datastructure,
      stable over time and return/extract operations.

      This datastructure adapt its capacity and resolution in time depending on the information flow and available
      storage size. by compressing semantically over equality of elements (events).
      Eventually this storage will drop oldest elements to keep things working... but the user cannot mutate it himself.

      Another layer on top (eventflow) can rely on the immutability of this class and test for a functional behavior
      to eventually use this storage as a cache...

      This is implemented by relying on a TimeLog for storage, but adds functionality of compressing the timeframe,
      and loose ordering information when  taking too much space. We leverage the monoidal structure of value type
      ( here an event counter ) for compression of the whole.

    """

    tlog: TimeLog  # keys are time clock in ns, value is an eventcounter.
    # needs to be "wrapped" to have keys being datetime (user perspective), providing unordered event counter as CRDT
    # TODO

    def __init__(self, store: typing.MutableMapping[int, EventCounter],  # TODO : support various structured data (type dict, pandas, etc.)
                 timer_ns: typing.Callable[[], int] = time.monotonic_ns, timeframe_ns: int = 1,
                 space_mem: typing.Callable[[typing.Any], int] = sys.getsizeof, resolution: int = 1):  # TODO : for space we should replace resolution with a hard bound
        # Time measurement
        self.timer_ns = timer_ns
        self.timeframe_ns = timeframe_ns
        # space measurement (memory / complexity, whichever makes most sense)
        self.space_mem = space_mem
        self.resolution = resolution

        self.tlog = TimeLog(mapping=store, inner_type=EventCounter, timer_ns=timer_ns, timeframe_ns=timeframe_ns)



        # self._inbatch = None
        # self._instamp = self.timer_ns()
        # self._edeq = OrderedDict()  # Note edeq is a usual ordered dict with exact keys
        # # TODO : not these ordered dict are actually sparse lists
        # #  ( maybe these can be related to sparse distribution representation and Hierarchical Temporal Memory? )
        # #    Ref : https://en.wikipedia.org/wiki/Sparse_distributed_memory
        # resampled_store = OrderedDict()  # TODO : specialise SpareTimeSeries to simplify code here ( think about SDM but with Nats instead of bool)...

        # # Note store are look for keys as approximated...
        # if store:
        #     # check that it matches the timeframe constraints
        #     for k, v in store:
        #         for kk, vv in reversed(resampled_store):
        #             if k - kk < timeframe_ns:  # if difference small, we combine counter:
        #                 resampled_store[kk] = resampled_store[kk] + v
        #                 break  # combo done, exit
        #             else:
        #                 resampled_store[k] = v
        #                 break
        #         else:  # first time when resampled_store is empty
        #             resampled_store[k] = v
        #     self._store = resampled_store
        # else:
        #     self._store = store

    def __bool__(self):  # same semantics as store for bool() (false if empty, true otherwise)
        return bool(self.tlog)

    def __sizeof__(self):
        size_code = self.space_mem(self.timer_ns) + self.space_mem(self.timeframe_ns) + self.space_mem(self.space_mem) + self.space_mem(self.resolution)
        size_tlog = self.space_mem(self.tlog) + sum(map(self.space_mem, self.tlog.keys())) + sum(map(self.space_mem, self.tlog.values()))
        return size_code + size_tlog

    def __call__(self):
        """ a sync write """

        appender = self.tlog()
        # TMP : simply forwarding the generator to timelog
        ti, ecount = appender.send(None)
        e = yield ti, ecount
        while True:
            try:
                ti, ecount = appender.send(e)
                e = yield ti, ecount
            except StopIteration as si:
                break



        #
        # now = self.timer_ns()
        # ti = TimeInterval(start=now, stop=now + self.timeframe_ns)
        # # if we already have a larger timeframe : use it
        # for k in self._l.keys():
        #     if now in k:
        #         ti = k
        #         break
        #
        # self._l[ti] = 0  # we need to initialize the accumulator/CRDT...
        #
        # now = self.timer_ns()
        # while ti.starts_inv(now) or now in ti:  # CAREFUL : END OF TIMEFRAME IS EXCLUDED : start of next timeframe
        #     new_v = yield ti, self._l[ti]
        #     if new_v is not None:
        #         self._l[ti] = self._l[ti] + new_v  # disordered accumulation semantics...
        #     # updating now before looping
        #     now = self.timer_ns()
        # return



        # now = self.timer_ns()
        # if self._inbatch is None:
        #     self._instamp = now
        #
        # # store current inbatch if needed
        # if self._inbatch is not None and now - self._instamp > self.timeframe_ns:
        #
        #     self._store[self._instamp] = self._inbatch
        #
        #     for s, e in self._edeq.items():
        #         if s < now:  # setting all events before now
        #             e.set()
        #         else:
        #             break  # stop now ! reminder : this is supposed to be ordered !
        #
        #     if not self._inbatch:  # no data -> not useful, maybe increase timeframe to get more data ?
        #         pass  # TODO maybe ?
        #     # reset
        #     self._inbatch = None
        #
        # if self._inbatch is None:
        #     self._inbatch = Counter()
        #
        # # in all cases: store in batch counter
        # if e in self._inbatch:
        #     self._inbatch[e] += 1  # add to counter
        #     # TODO : some counter bound to decide on timeframe
        #     # not useful because python has infinite integers...
        # else:
        #     self._inbatch[e] = 1
        #
        # return self

    def __len__(self):
        return len(self.tlog)

    def __contains__(self, item):
        for k, v in self.tlog.items():
            if k < item < k + self.timeframe_ns:
                return True
        return False

    def __getitem__(self, item):
        """ retrieve an observation (counter of events) in a timeframe """
        if isinstance(item, slice):
            # ordered dict doesnt support slicing (py 3.7) => manually
            #  we take care of start and stop here
            new_odict = OrderedDict([(k, v) for k, v in self._store.items()
                                     if k in list(self._store.keys())[item.start:item.stop] ])
            # slice step represent the timeframe, will be resampled at __init__
            new_tf = max(self.timeframe_ns, item.step)  # we can only downsample, not make things up...

            return eventstore(origin_store=new_odict,
                              timer_ns=self.timer_ns, timeframe_ns=new_tf,
                              space_mem=self.space_mem, resolution=self.resolution)
        else:
            for k, v in self._store.items():
                if k < item < k + self.timeframe_ns:
                    return v
            raise KeyError(f"{item} not in store")

    def __iter__(self):
        """ a sync non-blocking read... into the past ! """
        for e in self.tlog:  # note : tlog iterator already reversed !
            yield e

    # async def __aiter__(self):
    #     """ an async blocking read... into the future ! """
    #
    #     wait_for_content = asyncio.Event()
    #     while True:
    #
    #         now = self.timer_ns()
    #
    #         if not now in self:
    #             # before using we should clear the event in any case
    #             wait_for_content.clear()
    #             self._edeq[now] = wait_for_content
    #             await wait_for_content.wait()  # block until we get content
    #
    #         if now in self:
    #             s, e = self[now]
    #             yield e
    #
    #         if now in self._edeq:
    #             # remove event if needed
    #             self._edeq.pop(now)


def eventstore(timer_ns: typing.Callable[[], int] = time.monotonic_ns, timeframe_ns: int = 1,
                 space_mem: typing.Callable[[typing.Any], int] = sys.getsizeof, resolution: int = 1, origin_store=None):

        origin_store = origin_store if origin_store is not None else OrderedDict()

        return EventStore(store=origin_store, timer_ns=timer_ns, timeframe_ns=timeframe_ns,
                          space_mem=space_mem, resolution=resolution)


if __name__ == '__main__':
    # building intervals for testing
    dt1 = time.time_ns()
    time.sleep(1)
    dt2 = time.time_ns()
    time.sleep(1)
    dt3 = time.time_ns()
    time.sleep(1)
    dt4 = time.time_ns()

    til = [
        TimeInterval(dt1, dt2),
        TimeInterval(dt3, dt4)
    ]
    # values
    val = [2, 1]

    # example eventstore
    tl = eventstore(origin_store={t: i for t, i in zip(til, val)}, timeframe_ns=3000_000_000)

    # backward
    for t, e in tl:
        print(f"{t} : {e}")

    # forward
    extracted = []

    @dataclass(frozen=True)
    class TestEvent(Event):
        data: int


    acc = tl()

    curti, initv = acc.send(None)
    try:
        print()
        print(acc.send(TestEvent(42)))
        time.sleep(1)
        print(acc.send(TestEvent(42)))
        time.sleep(1)
        print(acc.send(TestEvent(53)))
        time.sleep(1)
        print(acc.send(TestEvent(33)))
        time.sleep(1)
        print(acc.send(TestEvent(33)))
        time.sleep(1)
        print(acc.send(TestEvent(33)))

    except StopIteration as si:
        print(f"{curti} ended already.")

    #
    # store = eventstore()
    #
    # def putin(i):
    #     print(f"putting {i}")
    #     store(i)
    #
    # putin(1)
    # putin(2)
    # putin(3)
    #
    # for e in store:
    #     print(f"{e}<<=")
    # # expecting
    # # 3
    # # 2
    # # 1
    #
    # async def getout():
    #     async for e in store:
    #         print(f"=>>{e}")
    #
    #
    # async def schedule():
    #
    #         asyncio.create_task(getout())
    #
    #         for i in range(1, 1024):
    #             await asyncio.sleep(0.5)
    #             # randomly put or pass
    #             if random.randint(0, 1):
    #                 putin(random.randint(0, 9))
    #             else:
    #                 pass
    #
    # asyncio.run(schedule())







