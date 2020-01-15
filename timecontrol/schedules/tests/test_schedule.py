import copy
import unittest
from dataclasses import dataclass, field
from datetime import datetime

from hypothesis import given, infer

from timecontrol.schedules.schedule import Intent, Schedule

import hypothesis.strategies as st


class TestIntent(unittest.TestCase):

    @given(ts=infer)
    def test_timestamp_from_integers(self, ts: int):
        e = Intent(targetdate=ts)

        assert hash(e) == hash(ts)

        # asserting reflexive equality (using copy to not have the same object)
        assert e == copy.copy(e)

    @given(ts=infer)
    def test_timestamp_from_datetime(self, ts: datetime):
        e = Intent(targetdate=ts)

        assert hash(e) == hash(ts)

        # asserting reflexive equality (using copy to not have the same object)
        assert e == copy.copy(e)

    @given(ts=infer)
    def test_equality_timestamp(self, ts: datetime):
        e1 = Intent(targetdate=ts)
        e2 = Intent(targetdate=ts)

        assert e1 == e2


class TestSchedule(unittest.TestCase):
    def timer(self):
        return self.clock

    def setUp(self) -> None:
        self.clock = 0

    def test_logger_mapping(self):
        # passing timer to log to simulate it
        f = Schedule()

        e1 = Intent(targetdate=self.clock+42)
        f[self.clock] = e1  # TODO : add possibiilty of naming ??

        assert {cr for cr in f()} == {e1}  # generating expectation from caller point of view

        e2 = Intent(targetdate=self.clock+42)
        f[self.clock] = e2

        assert f() == {e1} == {e2}  # since e1 == e2 - same timestamp

        self.clock += 43

        assert f() == set()  # no expectations

        e3 = Intent(targetdate=self.clock+53)
        f[self.clock] = e3

        assert f() == e3

        assert f.first == e3

    def test_logger_elems(self):
        @dataclass(frozen=True)
        class MyItt(Intent):
            value: int = field(default=0)

            def __hash__(self):
                return hash((super(MyItt, self).__hash__(), self.value))

        # Verifing indeterminism with advanced event type

        # passing timer to log to simulate it
        f = Schedule()

        e1 = MyItt(targetdate=self.clock+42, value=42)

        f[self.clock] = e1

        assert f() == {e1}  # generating expectation from caller point of view

        e2 = MyItt(targetdate=self.clock+42, value=51)

        f[self.clock] = e2

        assert f() == {e1, e2}  # since e1 != e2 - same timestamp


if __name__ == '__main__':
    unittest.main()
