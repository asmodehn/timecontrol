# A non empty list implemented on top of an functional (immutable) datastructure.
from __future__ import annotations
import typing
from collections.abc import Sequence
from dataclasses import dataclass

from pyrsistent import pvector, PVector


@dataclass(frozen=True, init=False, repr=False)
class DList(Sequence):
    """
    It looks like a list, it behaves like a list, but it is not exactly a list
    => it cannot be empty !
    """
    vector: PVector

    def __init__(self, l: typing.Iterable = None):
        l = l if l is not None else []
        object.__setattr__(self, 'vector', pvector(l))
        super(DList, self).__init__()

    def __repr__(self):
        return repr(list(self.vector))

    def __str__(self):
        return str(list(self.vector))

    def __getitem__(self, item: int):
        if item == 0:
            # Here we recurse (but only if user asks for it !)
            return DList()
        return self.vector[item - 1]

    def __len__(self):
        return len(self.vector) + 1


if __name__ == '__main__':

    dl = DList(['a', 'b', 'c'])

    assert len(dl) == 4

    assert dl[0] == DList()

    len(dl[0])

    print(dl[0][0])

    print(dl[1])
    print(dl[0][0])

    print(dl)
