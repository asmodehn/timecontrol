import unittest

from ..command import command, Command


class TestCommand(unittest.TestCase):

    def timer(self, incr=0):
        return self.clock

    def impl(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.command_call = False

    def test_command(self):
        c = command(self.impl, timer=self.timer)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, Command)

        assert len(c_one) == 0

        # one call will store in log
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result]

        # another call will store in same log again.
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result, self.result]

        # incrementing clock with create a new log
        old_clock = self.clock
        self.clock = 3

        c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == [self.result, self.result]
        assert c_one[self.clock] == [self.result]
