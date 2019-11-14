import unittest

from ..function import Function
from ..underlimiter import UnderLimiter, UnderTimeLimit


class TestUnderLimitedFunction(unittest.TestCase):

    def timer(self, incr=0):
        return self.clock

    def sleeper(self, slept):
        self.slept = slept
        # Note : to avoid blocking the sleep needs to directly modify the clock here
        self.clock += slept

    def funimpl(self, input):
        # ignoring input : constant function
        self.functional_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.functional_call = False

    def test_functionality_underlimit(self):
        lf = Function(UnderLimiter(period=3, timer=self.timer)(self.funimpl),
                      sleeper=self.sleeper)

        assert self.functional_call == False

        # Underlimit triggers and sleeps on *new* function calls
        assert lf[1] == 42
        assert self.slept == 3

        # But doesnt sleep on identical calls (using the cached value)
        self.slept = 0
        assert lf[1] == 42
        assert self.slept == 0

        # It will sleep on different calls
        assert lf[51] == 42
        assert self.slept == 3

        # Overall behaving as a forcibly-pure function. a Nice Abstraction.

