import unittest

import aiounittest

from ..command import Command, CommandRunner, CommandASyncRunner
from ..overlimiter import OverLimiter, OverTimeLimit


class TestOverLimitedCommand(aiounittest.AsyncTestCase):
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

    async def cmdimpl_coro(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.advanced = 0
        self.result = 42

        self.command_call = False

    async def test_command_overlimit(self):
        lc = Command(timer=self.timer, sleeper=self.sleeper)(
                OverLimiter(period=5, timer=self.timer)(self.cmdimpl)
        )

        assert self.command_call == False

        # Overlimit doesnt trigger for command instantiation
        lc_one = lc(1, "2", "etc")
        lc_two = lc(2, "42", "etc")
        assert isinstance(lc_one, CommandRunner)
        assert self.slept == 0

        assert len(lc_one) == 0

        # But triggers on command late run without sleeping
        self.clock += 7
        assert await lc_one() == 42
        assert self.slept == 0
        assert self.command_call == True
        assert len(lc_one) == 1

        # reset
        self.command_call = False

        # Has actually advanced the next call
        self.clock += (5 * 2 - self.clock)  # time to get to two periods as if there was no delay previously
        assert await lc_one() == 42
        assert self.slept == 0
        assert self.command_call == True
        assert len(lc_one) == 2
        assert lc_one._

        # reset
        self.command_call = False







        assert (
            lc_two() == 42
        )  # another call is also sleeping (sharing the command structure and therefore overlimiter)
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


    async def test_command_overlimit_coro(self):
        lc = OverLimiter(period=3, timer=self.timer)(
            Command(timer=self.timer, sleeper=self.sleeper)(self.cmdimpl_coro)
        )

        assert self.command_call == False

        # TODO
        raise NotImplementedError
