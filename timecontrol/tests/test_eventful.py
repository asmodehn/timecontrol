import asyncio

from timecontrol.eventful import eventful, CommandCalled, CommandReturned
import inspect
import unittest

import aiounittest

# TODO : test command called event
# TODO : test command returned event
from timecontrol.eventstore import EventStore


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

    @classmethod
    def class_cmdimpl(cls, *input, **extra):
        # ignoring input : constant function
        return 42

    @classmethod
    def class_genimpl(cls, *input, **extra):
        # ignoring input : deterministic generator
        yield 51
        yield 42
        return

    @staticmethod
    def static_cmdimpl(*input, **extra):
        # ignoring input : constant function
        return 42  # hardcoded return

    @staticmethod
    def statis_genimpl(*input, **extra):
        # ignoring input : deterministic generator
        yield 42
        yield 51
        return




    class EventSink(list):  # just a callable list storing whatever is passed to it.

        def __call__(self):
            while True:
                e = yield
                self.append(e)

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42
        self.events = list()
        # as far as the decorator is concerned, events are ordered (as per python semantics)

        self.command_call = False
        self.generator_call = False

    def test_eventful_pydef(self):
        sink = TestEventful.EventSink()  # careful class must be initialized here. we need to pass a callable
        lc = eventful(event_eradicator=sink, timer=self.timer, sleeper=self.sleeper)(self.cmdimpl)

        assert self.command_call == False

        # calling as usual
        lc_one = lc(1, "2", "etc")
        assert lc_one == 42

        assert self.command_call == True

        # log has been attached to the current class
        assert hasattr(self, "eventlog")
        assert self.cmdimpl.__name__ == lc.__name__  # wrapt is taking care of this
        assert self.cmdimpl.__name__ in self.eventlog

        # retrieving callevent in the log
        assert isinstance(self.eventlog[lc.__name__], TestEventful.EventSink)
        assert len(self.eventlog[lc.__name__]) == 2  # 2 events expected

        # return
        re = self.eventlog[lc.__name__][-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == 42

        # call
        ce = self.eventlog[lc.__name__][-2]
        assert isinstance(ce, CommandCalled)
        assert ("input", (1, "2", "etc")) in ce.bound_args

    # test static method (same as normal function)
    def test_eventful_pydef_static(self):
        sink = TestEventful.EventSink()  # careful class must be initialized here. we need to pass a callable
        lc = eventful(event_eradicator=sink, timer=self.timer, sleeper=self.sleeper)(self.static_cmdimpl)

        # calling as usual
        lc_one = lc(1, "2", "etc")
        assert lc_one == 42

        # log has been attached to the static function (like for a normal function
        assert hasattr(self.static_cmdimpl, "eventlog")

        # retrieving callevent in the log
        assert isinstance(self.static_cmdimpl.eventlog, TestEventful.EventSink)
        assert len(self.static_cmdimpl.eventlog) == 2  # 2 events expected

        # return
        re = self.static_cmdimpl.eventlog[-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == 42

        # call
        ce = self.static_cmdimpl.eventlog[-2]
        assert isinstance(ce, CommandCalled)
        assert ("input", (1, "2", "etc")) in ce.bound_args

    def test_eventful_pydef_class(self):
        sink = TestEventful.EventSink()  # careful class must be initialized here. we need to pass a callable
        lc = eventful(event_eradicator=sink, timer=self.timer, sleeper=self.sleeper)(TestEventful.class_cmdimpl)

        # calling as usual
        lc_one = lc(1, "2", "etc")
        assert lc_one == 42

        # log has been attached to the current class
        assert hasattr(self, "eventlog")
        assert self.cmdimpl.__name__ == lc.__name__  # wrapt is taking care of this
        assert self.cmdimpl.__name__ in self.eventlog

        # retrieving callevent in the log
        assert isinstance(self.eventlog[lc.__name__], TestEventful.EventSink)
        assert len(self.eventlog[lc.__name__]) == 2  # 2 events expected

        # return
        re = self.eventlog[lc.__name__][-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == 42

        # call
        ce = self.eventlog[lc.__name__][-2]
        assert isinstance(ce, CommandCalled)
        assert ("input", (1, "2", "etc")) in ce.bound_args


    def test_eventful_pygen(self):
        sink = TestEventful.EventSink()  # careful class must be initialized here. we need to pass a callable
        lc = eventful(event_eradicator=sink, timer=self.timer, sleeper=self.sleeper)(self.genimpl)

        assert self.generator_call == False

        # calling and getting call event
        lc_one = lc(1, "2", "etc")
        assert inspect.isgenerator(lc_one)
        # CAREFUL HERE ! GENERATOR HAS NOT BEEN actually CALLED UNTIL NEXT() !
        # This is in line with python semantics...
        assert self.generator_call == False

        # THEREFORE log is not created just yet

        # next() then triggers, and returns the result...
        ret = next(lc_one)
        assert ret == 1
        assert self.generator_call == True

        # log has been attached to the current class
        assert hasattr(self, "eventlog")
        assert self.genimpl.__name__ == lc.__name__  # wrapt is taking care of this
        assert self.genimpl.__name__ in self.eventlog

        # retrieving callevent and returnevent in the log
        assert isinstance(self.eventlog[lc.__name__], TestEventful.EventSink)
        assert len(self.eventlog[lc.__name__]) == 2  # 2 events expected

        # call
        ce = self.eventlog[lc.__name__][-2]
        assert isinstance(ce, CommandCalled)
        assert ("input", (1, "2", "etc")) in ce.bound_args

        # return
        re = self.eventlog[lc.__name__][-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == 1

        # next() then triggers, and returns the result...
        ret = next(lc_one)
        assert ret == 2
        assert self.generator_call == True

        # retrieving another rturnevent in the log
        assert isinstance(self.eventlog[lc.__name__], TestEventful.EventSink)
        assert len(self.eventlog[lc.__name__]) == 3  # 3 events expected

        # another return
        re = self.eventlog[lc.__name__][-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == 2

        # next() then doesnt work any longer
        with self.assertRaises(StopIteration) as si:
            next(lc_one)

    def test_eventful_pyclass(self):
        class_init = False
        class MyTstKls:
            def __init__(self, *input, **extra):
                nonlocal class_init
                class_init = True

        sink = TestEventful.EventSink()  # careful class must be initialized here. we need to pass a callable
        lc = eventful(event_eradicator=sink, timer=self.timer, sleeper=self.sleeper)(MyTstKls)

        assert class_init == False

        # Instantiating it as usual
        lc_one = lc(1, "2", "etc")
        assert isinstance(lc_one, MyTstKls)

        assert class_init == True

        # log has been attached to the class itself !
        assert hasattr(MyTstKls, "eventlog")
        assert MyTstKls.__name__ == lc.__name__  # wrapt is taking care of this
        # note we dont need multiple logs here (like for methods), class definition should be unique.

        # retrieving callevent in the log
        assert isinstance(MyTstKls.eventlog, TestEventful.EventSink)
        assert len(MyTstKls.eventlog) == 2  # 2 events expected

        # return
        re = MyTstKls.eventlog[-1]
        assert isinstance(re, CommandReturned)
        assert re.result and re.result.value == lc_one

        # call
        ce = MyTstKls.eventlog[-2]
        assert isinstance(ce, CommandCalled)
        assert ("input", (1, "2", "etc")) in ce.bound_args



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
