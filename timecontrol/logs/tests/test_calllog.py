import copy
import inspect
import unittest
from dataclasses import dataclass, field
from datetime import datetime

from hypothesis import given, infer

from ..calllog import CommandCalled, CallLog


import hypothesis.strategies as st


class TestCommandReturned(unittest.TestCase):

    @given(args=infer)
    def test_args_from_integers(self, args: int):

        sig= inspect.signature(lambda x: x)
        ba = sig.bind(args)

        called = CommandCalled(bound_arguments=ba)

        # asserting reflexive equality (using copy to not have the same object)
        assert called == copy.copy(called)

    @given(args=infer)
    def test_args_from_datetime(self, args: datetime):
        sig= inspect.signature(lambda x: x)
        ba = sig.bind(args)

        called = CommandCalled(bound_arguments=ba)

        # asserting reflexive equality (using copy to not have the same object)
        assert called == copy.copy(called)

    # TODO : test more args types...

    @given(kwargs=infer)
    def test_kwargs_from_integers(self, kwargs: int):
        sig= inspect.signature(lambda x: x)
        ba = sig.bind(kwargs)

        called = CommandCalled(bound_arguments=ba)

        # asserting reflexive equality (using copy to not have the same object)
        assert called == copy.copy(called)

    @given(kwargs=infer)
    def test_kwargs_from_datetime(self, kwargs: datetime):
        sig= inspect.signature(lambda x: x)
        ba = sig.bind(kwargs)

        called = CommandCalled(bound_arguments=ba)

        # asserting reflexive equality (using copy to not have the same object)
        assert called == copy.copy(called)

    # TODO : test more args types...


class TestCallLog(unittest.TestCase):
    def timer(self):
        return self.clock

    def setUp(self) -> None:
        self.clock = 0
        self.logged_call = False

    def test_logger_mapping(self):
        # passing timer to log to simulate it
        f = CallLog()

        sig= inspect.signature(lambda x: x)
        ba = sig.bind(42)

        e1 = CommandCalled(timestamp=self.clock, bound_arguments=ba)
        assert f(e1) == e1  # identity from caller point of view

        assert f[self.clock] == {e1}

        e2 = CommandCalled(timestamp=self.clock, bound_arguments=ba)
        assert f(e2) == e2

        assert f[self.clock] == {e1} == {e2}  # since e1 == e2 - same timestamp, different result

        self.clock += 1

        assert f[self.clock] == set()

        # change bound arguments !!!
        ba2 = sig.bind(51)

        e3 = CommandCalled(timestamp=self.clock, bound_arguments=ba2)
        assert f(e3) == e3

        assert f[self.clock] == {e3}

        e4 = CommandCalled(timestamp=self.clock, bound_arguments=ba)
        assert f(e4) == e4

        assert f[self.clock] == {e3, e4}  # since e3 != e4 - same timestamp, different result

        assert f.last in [ e3, e4]  # indeterminism !


if __name__ == '__main__':
    unittest.main()
