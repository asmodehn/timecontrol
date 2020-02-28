import inspect
import unittest

import aiounittest

from timecontrol.wrapper import eventful, CommandCalled, CommandReturned

# TODO : test command called
# TODO : test command returned


class TestEventful(aiounittest.AsyncTestCase):
    def timer(self):
        return self.clock

    def sleeper(self, slept):
        self.slept = slept
        # Note : to avoid blocking the sleep needs to directly modify the clock here
        self.clock += slept

    def cmdimpl(self, *input, **extra):
        # ignoring input : constant function
        self.command_call = True
        return self.result

    def genimpl(self, *input, **extra):
        # ignoring input : deterministic generator
        self.generator_call = True
        yield 1
        yield 2
        return

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.command_call = False
        self.generator_call = False

    def test_eventful_pydef(self):
        lc = eventful(timer=self.timer, sleeper=self.sleeper)(self.cmdimpl)

        assert self.command_call == False

        # calling and getting call event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        # next() returns the event of the call itself.
        assert isinstance(next(lc_one), CommandCalled)
        assert self.command_call == True

        # next() then triggers, and returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 42
        assert self.command_call == True

        # next() then doesnt work any longer
        with self.assertRaises(StopIteration) as si:
            next(lc_one)

        assert si.exception  # TODO : test exception details

    def test_eventful_pydef_ratelimit(self):
        lc = eventful(ratelimit=3, timer=self.timer, sleeper=self.sleeper)(self.cmdimpl)

        assert self.command_call == False

        # calling and getting first event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        assert self.slept == 0
        # next() returns the event of the call itself.
        assert isinstance(next(lc_one), CommandCalled)
        # after a bit of sleeping and calling
        assert self.slept == 3
        assert self.command_call == True

        # next() then returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 42
        assert self.slept == 3
        assert self.command_call == True

        # reset
        self.command_call = False
        self.slept = 0

        # calling again
        lc_two = lc(3, "4", "more")
        assert inspect.isgenerator(lc_two)
        assert self.slept == 0
        # next() returns the event of the call itself.
        assert isinstance(next(lc_two), CommandCalled)
        # after a bit of sleeping and calling
        assert self.slept == 3
        assert self.command_call == True

        # reset
        self.slept = 0
        self.command_call = False
        # increasing clock of more than a period
        self.clock += 4
        # next call will not sleep

        lc_three = lc(5, "6", "and more")
        assert inspect.isgenerator(lc_three)
        assert self.slept == 0
        # next() returns the event of the call itself.
        assert isinstance(next(lc_three), CommandCalled)
        # and calling without sleeping
        assert self.slept == 0
        assert self.command_call == True

    # TODO
    # def test_eventful_pydef_ratelimit_timeframe(self):
    #     raise NotImplementedError

    def test_eventful_pygen(self):
        lc = eventful(timer=self.timer, sleeper=self.sleeper)(self.genimpl)

        assert self.generator_call == False

        # calling and getting call event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        # next() returns the event of the call itself.
        assert isinstance(next(lc_one), CommandCalled)
        # CAREFUL HERE ! GENERATOR HAS NOT BEEN actually CALLED UNTIL NEXT() !
        # This is in line with python semantics... but different from usual pydef for our events !
        assert self.generator_call == False

        # next() then triggers, and returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 1
        assert self.generator_call == True

        # next() then triggers, and returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 2
        assert self.generator_call == True

        # next() then doesnt work any longer
        with self.assertRaises(StopIteration) as si:
            next(lc_one)

        assert si.exception  # TODO : test exception details

    # TODO
    # def test_eventful_pygen_ratelimit(self):
    #     raise NotImplementedError

    # TODO
    # def test_eventful_pygen_ratelimit_timeframe(self):
    #     raise NotImplementedError

    def test_eventful_pyclass(self):
        # TODO : a callable class must behave like a simple pydef on __call__
        #  Event should not mix with init/delete
        #  it would be the job of a higher-level eventful "concept" to do so,
        #  by wrapping the init in a pydef for example...

        cmd_call = False
        class MyTstKls:
            def __init__(self, res):
                self.res = res

            def __call__(self, *args, **kwargs):
                nonlocal cmd_call
                cmd_call = True
                return self.res

        LK = eventful(timer=self.timer, sleeper=self.sleeper)(MyTstKls)

        assert cmd_call == False

        # Instantiating it
        lc = LK(42)

        # calling and getting call event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        # next() returns the event of the call itself.
        assert isinstance(next(lc_one), CommandCalled)
        assert cmd_call == True

        # next() then triggers, and returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 42
        assert cmd_call == True

        # next() then doesnt work any longer
        with self.assertRaises(StopIteration) as si:
            next(lc_one)

        assert si.exception  # TODO : test exception details


    def test_eventful_pymeth(self):
        # TODO : a callable class must behave like a simple pydef on __call__
        #  Event should not mix with init/delete
        #  it would be the job of a higher-level eventful "concept" to do so,
        #  by wrapping the init in a pydef for example...

        cmd_call = False
        class MyTstKls:
            def __init__(self, res):
                self.res = res

            @eventful(timer=self.timer, sleeper=self.sleeper)
            def __call__(self, *args, **kwargs):
                nonlocal cmd_call
                cmd_call = True
                return self.res

        assert cmd_call == False

        # Instantiating it
        lc = MyTstKls(42)

        # calling and getting call event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        # next() returns the event of the call itself.
        assert isinstance(next(lc_one), CommandCalled)
        assert cmd_call == True

        # next() then triggers, and returns the result event...
        ret = next(lc_one)
        assert isinstance(ret, CommandReturned)
        assert ret.result and ret.result.value == 42
        assert cmd_call == True

        # next() then doesnt work any longer
        with self.assertRaises(StopIteration) as si:
            next(lc_one)

        assert si.exception  # TODO : test exception details

# TODO : ASYNC test !
# class TestAsyncEventful(TestEventful):
#
#     async def cmdimpl(self, *args):
#         # args ignored
#         self.command_call = True
#         return self.result
#
#     async def genimpl(self, *args):
#         # args ignored : deterministic generator
#         self.generator_call = True
#         yield 1
#         yield 2
#         return


if __name__ == '__main__':
    unittest.main()
