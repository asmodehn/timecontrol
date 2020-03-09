from __future__ import annotations

import itertools
import time
from asyncio import Event
from collections import OrderedDict
from collections.abc import Mapping
import typing

# TODO : generic span-key based mapping

# For now : timeinterval based dict
from datetime import datetime, timezone, timedelta

from timecontrol.timeinterval import TimeInterval, timeinterval, timep

class DistAgg:
    agg: int

    def __init__(self):
        self.agg = 0

    def __int__(self):
        return self.agg

    def __repr__(self):
        return repr(self.agg)

    def __str__(self):
        return str(self.agg)

    def __eq__(self, other: typing.Union[int, DistAgg]):
        if isinstance(other,int):
            return self.agg == other
        else:
            return self.agg == other.agg

    def __lt__(self, other: typing.Union[int, DistAgg]):
        if isinstance(other, int):
            return self.agg < other
        else:
            return self.agg < other.agg

    def __call__(self, v=1):
        # aggregating v. call order shouldnt matter !
        self.agg += v

    def merge(self, other):
        # merging aggregators
        self.agg = max ( self.agg, other.agg)


# TODO : timezone wrapper to depend onlocation => datetimelog

class TimeLog(Mapping):
    """
    This class implement a timeinterval based immutable mapping store (dict)
    We do not care here about values, that can be anything.

    Note: the keys could be sparsely distributed along the time axis...

    This datastructure can be called to start a generator that will store values in the current timeinterval, until the end of timeframe.
    The __call__() behaves like a bimonad into the future, where the iterator is a comonad into the (immutable) past.
    As a consequence, there is no notion of order inside a timeframe. => we need a CRDT-like data as value.

    """
    def __init__(self, mapping: typing.MutableMapping, inner_type=DistAgg,
                 timer_ns: typing.Callable[[], int] = time.time_ns, timeframe_ns: int = 1):
        # TODO : maybe the timer could be also an event loop timer for async code...
        # INTERNAL Time measurement (for in/out sync only)
        self.timer_ns = timer_ns
        self.timeframe_ns = timeframe_ns

        self._inner_type = inner_type

        self._l = OrderedDict(mapping)  # we need to enforce "some" ordering of the mapping, even if not present at first...
        self._wait = OrderedDict()  #  a dict of events, by timedate (timelog as well ??)

    @property
    def now_ns(self) -> int:
        return self.timer_ns()

    @property
    def begin(self) -> int:
        if self._l:
            return min(k.start for k in self._l.keys())
        else:
            return self.now_ns

    @property
    def end(self):
        if self._l:
            return max(k.stop for k in self._l.keys())
        else:
            return None  # no end yet... #TODO : proper semantics ?

    @property
    def timeindex(self):
        return (k for k in self._l.keys())

    @property
    def log(self):
        return (v for v in self._l.values())

    def __eq__(self, other):
        return all(k == kk and s == o for (k, s), (kk, o) in itertools.zip_longest(self, other))  # TODO : or just zip ?

    def __repr__(self):
        # howtodo repr ? some kind of ohlc ??
        return f"{self.begin}..{self.end} : {len(self._l.values())}"

    def __contains__(self, item: typing.Union[timep, TimeInterval]):
        if isinstance(item, timep):
            item = timeinterval(item)

        for k, v in self._l.items():
            if item in k:
                return True

    def __getitem__(self, item: typing.Union[timep, TimeInterval]):
        if isinstance(item, timep):
            item = timeinterval(item)

        # get item extract submapping of containing timespan
        res = OrderedDict()
        for k, v in self._l.items():
            if item in k:
                res[k] = v

        return timelog(res)  # pass the mapping directly

    # Immutable mapping except by calling, which is picky about args...
    # def __setitem__(self, key, value):
    #     if max(key, *self.timeindex) == key:
    #         self._l.setdefault(key, value)
    #         self._l[key] = value  # does the appropriate thing ...  # TODO : use typeddict
    #
    # def __delitem__(self, key):
    #     if min(key, self._l.keys()) == key:
    #         del self._l[key]

    def __len__(self):
        return len(self._l)

    def __iter__(self):  # extract past (immutable => non-blocking)
        for k, v in reversed(self._l.items()):
            yield k, v

    def __call__(self):
        now = self.timer_ns()
        ti = TimeInterval(start=now, stop=now + self.timeframe_ns)
        # if we already have a larger timeframe : use it
        for k in self._l.keys():
            if now in k:
                ti = k
                break

        self._l[ti] = self._inner_type()  # we need to initialize the accumulator/CRDT...

        now = self.timer_ns()
        while ti.starts_inv(now) or now in ti:  # CAREFUL : END OF TIMEFRAME IS EXCLUDED : start of next timeframe
            new_v = yield ti, self._l[ti]
            if new_v is not None:
                self._l[ti](new_v)  # disordered accumulation semantics...
            # updating now before looping
            now = self.timer_ns()
        return

    # async def __aiter__(self):  # extract future ( blocking )
    #     # CAREFUL : here we need the local timer to be related to the wallclock
    #     # TODO : monotonicity ??
    #     now = self.timer_ns()
    #
    #     # return current values for "now" if there is any (could be if stored and called in same timeframe)
    #     for k in self._l.keys():
    #         if now in k:
    #             yield k, self._l[k]
    #
    #     # then wait for next event
    #     wait_for_content = Event()
    #     while True:
    #         now = self.timer_ns()
    #
    #         if not now in self:
    #             # before using we should clear the event in any case
    #             wait_for_content.clear()
    #             self._wait[now] = wait_for_content
    #             await wait_for_content.wait()  # block until we get content
    #
    #         # we got content, yield it !
    #         for k in self._l.keys():
    #             if now in k:
    #                 yield k, self._l[k]
    #
    #         if now in self._wait:
    #             # remove event if needed
    #             self._wait.pop(now)


def timelog(mapping: typing.Mapping, timer_ns = time.time_ns, timeframe_ns = 1):
    if isinstance(mapping, TimeLog):
        # we have ot use the reverse of the items iterator to keep the order !
        od = OrderedDict(reversed([e for e in mapping]))  # TODO : or access internal mapping ?
    else:
        # to be able to grab data from any mapping, we use the items() interface
        od = OrderedDict(mapping.items())
    return TimeLog(od, timer_ns=timer_ns, timeframe_ns=timeframe_ns)


if __name__ == '__main__':
    # building intervals for testing
    dt1 = time.time_ns()
    time.sleep(1)
    dt2 =time.time_ns()
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

    # example timelog
    tl = timelog(mapping={t: i for t, i in zip(til, val)}, timeframe_ns=3000_000_000)

    # backward
    for t, e in tl:
        print(f"{t} : {e}")

    # forward
    extracted = []

    acc = tl()

    curti, initv = acc.send(None)
    try:
        print()
        print(acc.send(42))
        time.sleep(2)
        print(acc.send(42))
        time.sleep(2)
        print(acc.send(42))
    except StopIteration as si:
        print(f"{curti} ended already.")

    # print(acc.send(42))
    # for i, st in tl():
    #     print(f"=>> {st}")

    #
    # import asyncio
    # import random
    # loop = asyncio.get_event_loop()
    # t = loop.create_task(wait_loop_fwd())
    #
    # # We HAVE TO create the next interval after waiting for it
    # # otherwise we ll wait for ever since it has already happen, there will be nothing "new"
    #
    # # next value
    # nextt = timeinterval(time.time_ns())
    # nextv = 999  # special int value
    #
    # try :
    #     async def insert_n_loop():
    #         while nextv not in extracted:
    #             time.sleep(0.5)
    #             if not random.randint(0, 5):
    #                 print("inserting !")
    #                 tl(nextt, nextv)  # insert and wait for extraction
    #             else:
    #                 print("waiting...")
    #
    #     loop.run_until_complete(insert_n_loop())  # should exit when inserted value has ben extracted
    #
    #     # Here we are sure that we extracted what we wanted
    #     assert nextv in extracted
    #
    #     # cancel task.
    #     t.cancel()
    # except KeyboardInterrupt:
    #     t.result()
    # finally:
    #     loop.close()
