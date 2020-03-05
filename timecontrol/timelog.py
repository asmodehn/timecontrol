from __future__ import annotations

import itertools
import time
from asyncio import Event
from collections import Mapping, MutableMapping, OrderedDict

import typing

# TODO : generic span-key based mapping

# For now : timeinterval based dict
from datetime import datetime, timezone

from timecontrol.timeinterval import TimeInterval, timeinterval


class TimeLog(Mapping):
    """
    This class implement a timeinterval based immutable mapping store (dict)
    We do not care here about values, that can be anything.
    """
    def __init__(self, mapping: typing.Mapping,
                 timer_ns: typing.Callable[[], int] = time.monotonic_ns, timeframe_ns: int = 1):
        # INTERNAL Time measurement (for in/out sync only)
        self.timer_ns = timer_ns
        self.timeframe_ns = timeframe_ns

        self._l = mapping
        self._wait = OrderedDict()  #  a dict of events, by timedate (timelog as well ??)

    def __eq__(self, other):
        return all(k == kk and s == o for (k, s), (kk, o) in itertools.zip_longest(self, other))

    def __repr__(self):
        # howtodo repr ? some kind of ohlcv ??
        return f"{min(self._l.keys()).start}..{max(self._l.keys()).stop} : {len(self._l.values())}"

    def __contains__(self, item: typing.Union[datetime, TimeInterval]):
        if isinstance(item, datetime):
            item = timeinterval(item)

        for k, v in self._l.items():
            if item in k:
                return True

    def __getitem__(self, item: typing.Union[datetime, TimeInterval]):
        if isinstance(item, datetime):
            item = timeinterval(item)

        # get item extract submapping of containing timespan
        res = OrderedDict()
        for k, v in self._l.items():
            if item in k:
                res[k] = v

        return timelog(res)  # pass the mapping directly

    def __len__(self):
        return len(self._l)

    def __iter__(self):  # extract past (immutable => non-blocking)
        for k, v in reversed(self._l.items()):
            yield k, v

    async def __aiter__(self):  # extract future ( blocking )

        now = datetime.fromtimestamp(self.timer_ns(), tz=timezone.utc)

        async for k, v in self[now]:
            yield k, v
        # then wait for next event
        wait_for_content = Event()
        while True:
            now = datetime.fromtimestamp(self.timer_ns(), tz = timezone.utc)

            if not now in self:
                # before using we should clear the event in any case
                wait_for_content.clear()
                self._wait[now] = wait_for_content
                await wait_for_content.wait()  # block until we get content

            # we got content, yield it !
            async for k, v in self[now]:
                yield k, v

            if now in self._wait:
                # remove event if needed
                self._wait.pop(now)


EmptyTimeLog = TimeLog(mapping=OrderedDict())


# Note : timelog is immutable
def timelog(mapping: typing.Mapping):
    if not mapping:
        return EmptyTimeLog

    if isinstance(mapping, TimeLog):
        # we have ot use the reverse of the items iterator to keep the order !
        od = OrderedDict(reversed([e for e in mapping]))  # TODO : or access internal mapping ?
    else:
        # to be able to grab data from any mapping, we use the items() interface
        od = OrderedDict(mapping.items())
    return TimeLog(od)


if __name__ == '__main__':
    pass