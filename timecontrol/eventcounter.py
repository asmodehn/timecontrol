import sys
from collections import Counter
from dataclasses import dataclass

# enforcing event properties (immutable / hashable)
@dataclass(frozen=True, init=False)
class Event:
    pass


# to enforce unicity of instance (all instance are equal => no point to have more than one of them)
TheEvent = Event()


def event():
    return TheEvent


class EventCounter(Counter):

    def __sizeof__(self):
        supersize = sys.getsizeof(super)
        # adding content size
        s = supersize + sum(sys.getsizeof(k) for k in self.keys()) + sum(sys.getsizeof(v) for v in self.values())
        return s


if __name__ == '__main__':
    pass
