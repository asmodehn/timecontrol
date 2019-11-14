import unittest

from ..command import command, Command
from ..underlimiter import UnderLimiter, UnderTimeLimit


class TestUnderLimitedCommand(unittest.TestCase):

    def timer(self, incr=0):
        return self.clock

    def sleeper(self, slept):
        self.slept = slept
        # Note : to avoid blocking the sleep needs to directly modify the clock here
        self.clock += slept

    def cmdimpl(self, *input):
        # ignoring input : constant function
        self.command_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.command_call = False

    def test_command_underlimit(self):
        lc = command(UnderLimiter(period=3, timer=self.timer)(self.cmdimpl),
                     timer=self.timer,
                     sleeper=self.sleeper)

        assert self.command_call == False

        # Underlimit doesnt trigger for command instantiation
        lc_one = lc(1, "2", "etc")
        lc_two = lc(2, "42", "etc")
        assert isinstance(lc_one, Command)
        assert self.slept == 0

        assert len(lc_one) == 0

        # But triggers, and sleeps on command run...
        assert lc_one() == 42
        assert self.slept == 3
        assert self.command_call == True
        assert len(lc_one) == 1

        # reset
        self.command_call = False

        assert lc_two() == 42  # another call is also sleeping (sharing the command structure and therefore underlimiter)
        assert self.slept == 3
        assert self.command_call == True
        assert len(lc_two) == 1  # NOT sharing the time log

        # reset
        self.slept = 0
        self.command_call = False
        # increasing clock of more than a period
        self.clock += 4
        # next call will not sleep

        assert lc_one() == 42
        assert self.slept == 0
        assert self.command_call == True

