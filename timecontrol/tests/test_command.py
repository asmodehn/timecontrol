from ..command import Command, CommandRunner, CommandASyncRunner

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

    async def test_command(self):
        # bound method or usual procedure usecase
        c = Command(timer=self.timer)(self.impl)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, CommandASyncRunner)

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result}

        # another call will store in same log again.
        old_result = self.result
        self.result = 51
        # works here (compared to other test), because function implementation stores a reference to the value...

        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result, old_result}

        self.result = old_result  # reset
        old_result = 51
        # incrementing clock with create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == {self.result, old_result}
        assert c_one[self.clock] == {self.result}

    async def test_command_coro(self):
        # bound method or usual procedure usecase
        c = Command(timer=self.timer)(self.impl_coro)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, CommandASyncRunner)

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result}

        # another call will store in same log again.
        old_result = self.result
        self.result = 51
        # works here (compared to other test), because function implementation stores a reference to the value...

        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result, old_result}

        self.result = old_result  # reset
        old_result = 51
        # incrementing clock with create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == {self.result, old_result}
        assert c_one[self.clock] == {self.result}

    async def test_command_method(self):
        # instance method usecase
        test_result = self.result

        class Sample:
            def __init__(self):
                self.method_call = False
                self.result = test_result

            @Command(timer=self.timer)
            def method(self, *args):
                self.method_call = True
                return self.result

        sample = Sample()

        assert sample.method_call == False
        c_one = sample.method(1, "2", "etc")
        assert isinstance(c_one, CommandASyncRunner)
        assert sample.method_call == False

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result}

        # another call will store in same log again.
        old_result = sample.result
        sample.result = 51
        # here we need to change the result variable in the instance (an actual copy of self.result)

        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {sample.result, old_result}

        sample.result = old_result  # reset
        old_result = 51
        # incrementing clock will create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == {self.result, old_result}
        assert c_one[self.clock] == {self.result}

    async def test_command_method_coro(self):
        # instance method usecase
        test_result = self.result

        class Sample:
            def __init__(self):
                self.method_call = False
                self.result = test_result

            @Command(timer=self.timer)
            async def method(self, *args):
                self.method_call = True
                return self.result

        sample = Sample()

        assert sample.method_call == False
        c_one = sample.method(1, "2", "etc")
        assert isinstance(c_one, CommandASyncRunner)
        assert sample.method_call == False

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result}

        # another call will store in same log again.
        old_result = sample.result
        sample.result = 51
        # here we need to change the result variable in the instance (an actual copy of self.result)

        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {sample.result, old_result}

        sample.result = old_result  # reset
        old_result = 51
        # incrementing clock will create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == {self.result, old_result}
        assert c_one[self.clock] == {self.result}

    async def test_command_class(self):
        test_result = self.result

        @Command(timer=self.timer)
        class Sample:
            def __init__(self):
                self.call_call = False
                self.result = test_result

            def __call__(self, *args, **kwargs):
                self.call_call = True
                return self.result

        sample = Sample()

        assert sample.call_call == False
        c_one = sample(1, "2", "etc")
        assert isinstance(c_one, CommandASyncRunner)
        assert sample.call_call == False

        assert len(c_one) == 0

        # one call will store in log
        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {self.result}

        # another call will store in same log again.
        old_result = c_one._impl.result
        c_one._impl.result = 51
        # here we need to change the result variable in the COMMAND instance (an actual copy of self.result)

        await c_one()
        assert len(c_one) == 1
        assert c_one[self.clock] == {c_one._impl.result, old_result}

        c_one._impl.result = old_result  # reset
        old_result = 51
        # incrementing clock will create a new log
        old_clock = self.clock
        self.clock = 3

        await c_one()
        assert len(c_one) == 2
        assert c_one[old_clock] == {self.result, old_result}
        assert c_one[self.clock] == {self.result}
