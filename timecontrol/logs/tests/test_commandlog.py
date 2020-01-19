import copy
import unittest
from datetime import datetime

import aiounittest
from hypothesis import given, infer
import  hypothesis.strategies as st
from result import Result

from timecontrol.logs.commandlog import CommandRun, CommandLog
from timecontrol.logs.resultlog import CommandReturned


class TestCommandRun(unittest.TestCase):

    @given(result=infer)
    def test_result_from_integers(self, result: int):
        ok = CommandRun(result=Result.Ok(result))
        err = CommandRun(result=Result.Err(result))

        # asserting reflexive equality (using copy to not have the same object)
        assert ok == copy.copy(ok)
        assert err == copy.copy(err)
        assert ok != err

    @given(result=infer)
    def test_timestamp_from_datetime(self, result: datetime):
        ok = CommandRun(result=Result.Ok(result))
        err = CommandRun(result=Result.Err(result))

        # asserting reflexive equality (using copy to not have the same object)
        assert ok == copy.copy(ok)
        assert err == copy.copy(err)
        assert ok != err

    # TODO : test more result types...

    # TODO : test args !!!


# Here we need to validate commandlog behavior with async calls...

class TestCommandLog(unittest.TestCase):

    def timer(self):
        return self.clock

    def setUp(self) -> None:
        self.clock = 0
        self.logged_call = False

    def test_logger_mapping(self):
        # passing timer to log to simulate it
        f = CommandLog()

        e1 = CommandRun(timestamp=self.clock, result=Result.Ok(42))
        assert f(e1) == e1  # identity from caller point of view

        assert f[self.clock] == {e1}

        e2 = CommandRun(timestamp=self.clock, result=Result.Ok(42))
        assert f(e2) == e2

        assert f[self.clock] == {e1} == {e2}  # since e1 == e2 - same content

        self.clock += 1

        assert f[self.clock] == set()

        e3 = CommandRun(timestamp=self.clock, result=Result.Ok(42))
        assert f(e3) == e3

        assert f[self.clock] == {e3}

        assert f.last == e3
    