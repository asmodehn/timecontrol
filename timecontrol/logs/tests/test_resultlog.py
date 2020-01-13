import copy
import unittest
from dataclasses import dataclass, field
from datetime import datetime

from hypothesis import given, infer

from ..resultlog import Result, CommandReturned, ResultLog


import hypothesis.strategies as st


class TestCommandReturned(unittest.TestCase):

    @given(result=infer)
    def test_result_from_integers(self, result: int):
        ok = CommandReturned(result=Result.Ok(result))
        err = CommandReturned(result=Result.Err(result))

        # asserting reflexive equality (using copy to not have the same object)
        assert ok == copy.copy(ok)
        assert err == copy.copy(err)
        assert ok != err

    @given(result=infer)
    def test_timestamp_from_datetime(self, result: datetime):
        ok = CommandReturned(result=Result.Ok(result))
        err = CommandReturned(result=Result.Err(result))

        # asserting reflexive equality (using copy to not have the same object)
        assert ok == copy.copy(ok)
        assert err == copy.copy(err)
        assert ok != err

    # TODO : test more result types...


class TestResultLog(unittest.TestCase):
    def timer(self):
        return self.clock

    def setUp(self) -> None:
        self.clock = 0
        self.logged_call = False

    def test_logger_mapping(self):
        # passing timer to log to simulate it
        f = ResultLog()

        e1 = CommandReturned(timestamp=self.clock, result=Result.Ok(42))
        assert f(e1) == e1  # identity from caller point of view

        assert f[self.clock] == {e1}

        e2 = CommandReturned(timestamp=self.clock, result=Result.Ok(42))
        assert f(e2) == e2

        assert f[self.clock] == {e1} == {e2}  # since e1 == e2 - same timestamp, different result

        self.clock += 1

        assert f[self.clock] == set()

        e3 = CommandReturned(timestamp=self.clock, result=Result.Ok(51))
        assert f(e3) == e3

        assert f[self.clock] == {e3}

        e4 = CommandReturned(timestamp=self.clock, result=Result.Ok(42))
        assert f(e4) == e4

        assert f[self.clock] == {e3, e4}  # since e3 != e4 - same timestamp, different result

        assert f.last in [ e3, e4]  # indeterminism !


if __name__ == '__main__':
    unittest.main()
