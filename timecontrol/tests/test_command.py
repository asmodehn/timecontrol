

from ..command import Command, CommandRunner

import aiounittest


class TestCommand(aiounittest.AsyncTestCase):

    def timer(self, incr=0):
        return self.clock

    def impl(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    async def impl_coro(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.command_call = False

    def test_command(self):
        # bound method or usual procedure usecase
        c = Command(timer=self.timer)(self.impl)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, CommandRunner)

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

    async def test_command_coro(self):
        # bound method or usual procedure usecase
        c = Command(timer=self.timer)(self.impl_coro)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, CommandRunner)

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result]

        # another call will store in same log again.
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result, self.result]

        # incrementing clock with create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == [self.result, self.result]
        assert c_one[self.clock] == [self.result]

    def test_command_method(self):
        # instance method usecase
        test_result = self.result
        class Sample:
            def __init__(self):
                self.method_call = False

            @Command(timer=self.timer)
            def method(self, *args):
                self.method_call = True
                return test_result

        sample = Sample()

        assert sample.method_call == False
        c_one = sample.method(1, "2", "etc")
        assert isinstance(c_one, CommandRunner)
        assert sample.method_call == False

        assert len(c_one) == 0

        # one call will store in log
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result]

        # another call will store in same log again.
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result, self.result]

        # incrementing clock will create a new log
        old_clock = self.clock
        self.clock = 3

        c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == [self.result, self.result]
        assert c_one[self.clock] == [self.result]

    def test_command_class(self):
        test_result = self.result

        @Command(timer=self.timer)
        class Sample:
            def __init__(self):
                self.call_call = False

            def __call__(self, *args, **kwargs):
                self.call_call = True
                return test_result

        sample = Sample()

        assert sample.call_call == False
        c_one = sample(1, "2", "etc")
        assert isinstance(c_one, CommandRunner)
        assert sample.call_call == False

        assert len(c_one) == 0

        # one call will store in log
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result]

        # another call will store in same log again.
        c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == [self.result, self.result]

        # incrementing clock will create a new log
        old_clock = self.clock
        self.clock = 3

        c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == [self.result, self.result]
        assert c_one[self.clock] == [self.result]



# TODO : ASync !