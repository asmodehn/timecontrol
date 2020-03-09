import sys
from collections import Counter
from collections.abc import MutableMapping
from dataclasses import dataclass

# enforcing event properties (immutable / hashable)
from timecontrol.countinterval import countinterval


@dataclass(frozen=True, init=False)
class Event:
    pass


# to enforce unicity of instance (all instance are equal => no point to have more than one of them)
TheEvent = Event()


def event():
    return TheEvent


class EventCounter(MutableMapping):

    # to manage uncertainty, allow only converging mutations
    high: Counter
    low: Counter
    # leveraging counter collection instead of dict of interval as values

    def __init__(self, low:Counter = None, high:Counter = None):
        if high is None and low is None:
            self.high = Counter()
            self.low = Counter()
        elif high is None:
            self.high = low
            self.low = low
        elif low is None:
            self.high = high
            self.low = high
        else:
            self.high = high
            self.low = low

    def __call__(self, e:Event):
        """
        An event certified observed.
        :param e:
        :return:
        """
        self.low[e] +=1
        self.high[e] +=1

        return self

    def __repr__(self):
        reprstr = f"EventCounter<"
        for e in self.low.keys():
            reprstr += f"{e} : [{self.low[e]}..{self.high[e]}], "
        return reprstr

    def __getitem__(self, item):
        return countinterval(self.low[item], self.high[item])

    def __setitem__(self, key, value):
        # set if not there
        self.low.setdefault(key, value)
        self.high.setdefault(key, value)
        # set if inside the interval (convergence only is allowed)
        if self.low[key] < value:
            self.low[key] = value
        if self.high[key] > value:
            self.high[key] = value
        # else ignore. if doing merging/addition of counter -> create new counter

    def __delitem__(self, key):
        del self.high[key]
        del self.low[key]

    def __iter__(self):
        for e, c in self.low:  # Note: high and low should always be in sync !
            yield e, countinterval(c, self.high[e])

    def __len__(self):
        return max(len(self.high), len(self.low))

    def __sizeof__(self):
        highsize = sys.getsizeof(self.high)
        lowsize = sys.getsizeof(self.low)
        # adding content size
        sh = highsize + sum(sys.getsizeof(k) for k in self.high.keys()) + sum(sys.getsizeof(v) for v in self.high.values())
        sl = lowsize + sum(sys.getsizeof(k) for k in self.low.keys()) + sum(sys.getsizeof(v) for v in self.low.values())
        return sh + sl

    # TODO Counter API with interval semantics for content

    def __add__(self, other):
        """ adds counter together.
        """
        return EventCounter(low= self.low + other.low, high=self.high + other.high)

    # def __and__(self, other):
    #     """"""
    #     return EventCounter(low=self.low & other.low)

if __name__ == '__main__':
    pass
