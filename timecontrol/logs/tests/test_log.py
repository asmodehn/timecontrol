import copy
import unittest
from dataclasses import dataclass, field
from datetime import datetime

from hypothesis import given, infer

from ..log import Event, Log

import hypothesis.strategies as st


class TestEvent(unittest.TestCase):

    @given(ts=infer)
    def test_timestamp_from_integers(self, ts: int):
        e = Event(timestamp=ts)

        assert hash(e) == hash(ts)

        # asserting reflexive equality (using copy to not have the same object)
        assert e == copy.copy(e)

    @given(ts=infer)
    def test_timestamp_from_datetime(self, ts: datetime):
        e = Event(timestamp=ts)

        assert hash(e) == hash(ts)

        # asserting reflexive equality (using copy to not have the same object)
        assert e == copy.copy(e)

    @given(ts=infer)
    def test_equality_timestamp(self, ts: datetime):
        e1 = Event(timestamp=ts)
        e2 = Event(timestamp=ts)

        assert e1 == e2


class TestLog(unittest.TestCase):
    def timer(self):
        return self.clock

    def setUp(self) -> None:
        self.clock = 0

    def test_logger_mapping(self):
        # passing timer to log to simulate it
        f = Log()

        e1 = Event(timestamp=self.clock)
        assert f(e1) == e1  # identity from caller point of view

        assert f[self.clock] == {e1}

        e2 = Event(timestamp=self.clock)
        assert f(e2) == e2

        assert f[self.clock] == {e1} == {e2}  # since e1 == e2 - same timestamp

        self.clock += 1

        assert f[self.clock] == set()

        e3 = Event(timestamp=self.clock)
        assert f(e3) == e3

        assert f[self.clock] == {e3}

        assert f.last == e3

    def test_logger_elems(self):
        @dataclass(frozen=True)
        class MyEvt(Event):
            value: int = field(default=0)

            def __hash__(self):
                return hash((super(MyEvt, self).__hash__(), self.value))

        # Verifing indeterminism with advanced event type

        # passing timer to log to simulate it
        f = Log()

        e1 = MyEvt(timestamp=self.clock, value=42)
        assert f(e1) == e1  # identity from caller point of view

        assert f[self.clock] == {e1}

        e2 = MyEvt(timestamp=self.clock, value=51)
        assert f(e2) == e2

        assert f[self.clock] == {e1, e2}  # since e1 != e2 - same timestamp


if __name__ == '__main__':
    unittest.main()
