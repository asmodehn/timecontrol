
import unittest
from typing import Generator, Sequence


# Just an example to make sure we understand how an Iterator works first
from timecontrol.utils.aggregator import Aggregator, aggr, drop


# Ref : https://docs.python.org/3/library/stdtypes.html#typeiter
class MyIterator:
    def __init__(self, sequence: Sequence, start=0):
        self.sequence = sequence
        self.index = start

    def __iter__(self):  # seems needed to be usable in a for . in .: construct like the result of iter()
        return self

    def __next__(self):
        self.index = self.index + 1
        try:
            return self.sequence[self.index -1]
        except IndexError:
            raise StopIteration


class TestIterate(unittest.TestCase):

    def test_iter_drives(self):
        l = [1,2,3]
        myit = MyIterator(l)

        it = iter(l)
        for v in it:
            assert next(myit) == v

    def test_myit_drives(self):
        l = [1,2,3]
        it = iter(l)

        myit = MyIterator(l)
        for v in myit:
            assert next(it) == v


class TestListAggregator(unittest.TestCase):

    def test_ListAggregator(self):
        l = []
        myag = aggr(l)

        for v in range(5):
            drop(myag, v)  # consumes/dissipates v into the underlying list

        assert myag == [0, 1, 2, 3, 4]  # aggregator contains all values
        assert l == []  # list l didn't change (just like iterator doesnt change original sequence)

    def test_DictAggregator(self):
        d = {}
        myag = aggr(d)

        for v in range(5):
            drop(myag, v)    # consumes/dissipates v into the underlying dict

        assert [v for v in myag.values()] == [0, 1, 2, 3, 4]
        assert d == {}


if __name__ == '__main__':
    unittest.main()
