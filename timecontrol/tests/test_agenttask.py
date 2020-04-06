import asyncio
import inspect
import unittest

# The five types of functions in python, for test
import typing
import wrapt
from hypothesis import given, infer
import hypothesis.strategies as st

from timecontrol.agenttask import fun2coro, delayed


def function_test(*args, **kwargs):
    return args, kwargs


async def coroutine_test(*args, **kwargs):
    return args, kwargs


def generator_test(*args, **kwargs):
    for a in (args, kwargs):
        yield a
    return  # Note : a generator can return a value, but it is just another yield within a stop iteration.


async def async_generator_test(*args, **kwargs):
    for a in (args, kwargs):
        yield a
    return  # py 3.7 : an async generator cannot return a value.


# Notice : This is a Function watching a generator, and returning what was yielded
def generator_watcher(watched: typing.Generator, *args, **kwargs):
    gen = watched
    res_args = gen.send(None)
    assert res_args == args
    res_kwargs = gen.send(None)
    assert res_kwargs == kwargs
    # testing the return
    try:
        gen.send(None)
        raise RuntimeError("TEST FAILED ! Expected StopIteration Exception not raised")
    except StopIteration as si:
        assert si.args == ()
        return res_args, res_kwargs
    # No StopIteration, no return -> trigger test fail


# Notice : This is a Coroutine watching an awaitable generator, and returning what was yielded
async def awaitable_generator_watcher(watched: typing.Coroutine, *args, **kwargs):
    gen = await watched
    res_args = gen.send(None)
    assert res_args == args
    res_kwargs = gen.send(None)
    assert res_kwargs == kwargs
    # testing the return
    try:
        gen.send(None)
        raise RuntimeError("TEST FAILED ! Expected StopIteration Exception not raised")
    except StopIteration as si:
        assert si.args == ()
        return res_args, res_kwargs
    # No StopIteration, no return -> trigger test fail


# Notice : This is a Coroutine watching an async generator, and returning what was yielded
async def async_generator_watcher(watched: typing.AsyncGenerator, *args, **kwargs):
    gen = watched  # object async_generator can't be used in 'await' expression
    # TODO: debug this (somehow not like an awaitable generator ?)
    res_args = await gen.asend(None)
    assert res_args == args
    res_kwargs = await gen.asend(None)
    assert res_kwargs == kwargs
    # return has to be None (py3.7)
    # testing the return
    try:
        await gen.asend(None)
        raise RuntimeError("TEST FAILED ! Expected StopAsyncIteration Exception not raised")
    except StopAsyncIteration as sai:
        assert sai.args == ()
        return res_args, res_kwargs
    # No StopAsyncIteration, no return -> trigger test fail


# Notice : This is a Coroutine watching an async generator, and returning what was yielded
async def awaitable_async_generator_watcher(watched: typing.Coroutine, *args, **kwargs):  # typing.AwaitableAsyncGenerator
    gen = await watched
    # TODO: debug this (somehow not like an awaitable generator ?)
    res_args = await gen.asend(None)
    assert res_args == args
    res_kwargs = await gen.asend(None)
    assert res_kwargs == kwargs
    # return has to be None (py3.7)
    # testing the return
    try:
        await gen.asend(None)
        raise RuntimeError("TEST FAILED ! Expected StopAsyncIteration Exception not raised")
    except StopAsyncIteration as sai:
        assert sai.args == ()
        return res_args, res_kwargs
    # No StopAsyncIteration, no return -> trigger test fail

class ClassMethodTest:

    def method(self, *args, **kwargs):
        return args, kwargs


class TestFun2Coro(unittest.TestCase):

    @given(args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_fun2coro_function(self, *args, **kwargs):
        cf = fun2coro(function_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert inspect.iscoroutine(cc)
        resa, reskwa = asyncio.run(cc)
        assert resa == args
        assert reskwa == kwargs

    @given(args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_fun2coro_coroutine(self, *args, **kwargs):
        cf = fun2coro(coroutine_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert inspect.iscoroutine(cc)
        resa, reskwa = asyncio.run(cc)
        assert resa == args
        assert reskwa == kwargs

    @given(args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_fun2coro_generator(self, *args, **kwargs):
        cf = fun2coro(generator_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert inspect.iscoroutine(cc)
        # passing same args and kwargs to watcher for asserting
        resa, reskwa = asyncio.run(awaitable_generator_watcher(cc, *args, **kwargs))
        assert resa == args
        assert reskwa == kwargs

    @given(args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_fun2coro_async_generator(self, *args, **kwargs):
        cf = fun2coro(async_generator_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert inspect.isasyncgen(cc)  # NOT a coroutine for python !
        # passing same args and kwargs to watcher for asserting
        resa, reskwa = asyncio.run(async_generator_watcher(cc, *args, **kwargs))
        assert resa == args
        assert reskwa == kwargs

    @given(args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_fun2coro_classmethod(self, *args, **kwargs):
        # test decorating the method (doing it functionally for tests)
        ClassMethodTest.decmeth = fun2coro(ClassMethodTest.method)
        assert isinstance(ClassMethodTest.decmeth, wrapt.BoundFunctionWrapper)

        # Instantiation of the class (must be in sync code !)
        ci = ClassMethodTest()

        # calling it as a method
        cc = ci.decmeth(*args, **kwargs)
        assert inspect.iscoroutine(cc)
        resa, reskwa = asyncio.run(cc)
        assert resa == args
        assert reskwa == kwargs

    #TODO : decorating the class itself ? what semantics ? like decorating __init__ ? like a meta class, smthg else ? *typeclass* ?


class TestDelayed(unittest.TestCase):

    def syncsleep(self, delay):
        print(delay)
        self.delayed += delay

    async def asyncsleep(self, delay):
        self.adelayed += delay

    @given(delay=st.floats(allow_nan=False, allow_infinity=False, min_value=0.01),
           args=st.integers(),
           kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_delayed_function(self, delay, *args, **kwargs):
        # obvious setup
        self.delayed = 0.0
        self.adelayed = 0.0

        cf = delayed(delay=delay, sleeper=self.syncsleep)(function_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert self.delayed == delay
        assert self.adelayed == 0.0
        resa, reskwa = cc
        assert resa == args
        assert reskwa == kwargs

    @given(delay=st.floats(allow_nan=False, allow_infinity=False),
           args=st.integers(),
           kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_delayed_coroutine(self, delay, *args, **kwargs):
        # obvious setup
        self.delayed = 0.0
        self.adelayed = 0.0

        cf = delayed(delay=delay, sleeper=self.asyncsleep)(coroutine_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert self.delayed == 0.0
        assert self.adelayed == 0.0
        assert inspect.iscoroutine(cc)
        resa, reskwa = asyncio.run(cc)
        assert self.delayed == 0.0
        assert self.adelayed == delay
        assert resa == args
        assert reskwa == kwargs

    @given(delay=st.floats(allow_nan=False, allow_infinity=False),
           args=st.integers(),
           kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_delayed_generator(self, delay, *args, **kwargs):
        # obvious setup
        self.delayed = 0.0
        self.adelayed = 0.0

        cf = delayed(delay=delay, sleeper=self.syncsleep)(generator_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert self.delayed == delay  # already delayed here, before starting generator.
        assert self.adelayed == 0.0
        assert inspect.isgenerator(cc)
        # passing same args and kwargs to watcher for asserting
        resa, reskwa = generator_watcher(cc, *args, **kwargs)
        assert self.delayed == delay  # This was just a starting delay, not a throttle in generator loop.
        assert self.adelayed == 0.0
        assert resa == args
        assert reskwa == kwargs

    @given(delay=st.floats(allow_nan=False, allow_infinity=False),
           args=st.integers(),
           kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_delayed_async_generator(self, delay, *args, **kwargs):
        # obvious setup
        self.delayed = 0.0
        self.adelayed = 0.0

        cf = delayed(delay=delay, sleeper=self.asyncsleep)(async_generator_test)
        assert isinstance(cf, wrapt.FunctionWrapper)
        cc = cf(*args, **kwargs)
        assert self.delayed == 0.0
        assert self.adelayed == 0.0
        assert inspect.iscoroutine(cc)  # IS a coroutine ! wrapping an asyncgen !
        # passing same args and kwargs to watcher for asserting
        resa, reskwa = asyncio.run(awaitable_async_generator_watcher(cc, *args, **kwargs))
        assert self.delayed == 0.0
        assert self.adelayed == delay  # This was just a starting delay, not a throttle in generator loop
        assert resa == args
        assert reskwa == kwargs

    @given(delay=st.floats(allow_nan=False, allow_infinity=False),
           args=st.integers(), kwargs=st.dictionaries(keys=st.text(max_size=5), values=st.integers()))
    def test_delayed_classmethod(self, delay, *args, **kwargs):
        # obvious setup
        self.delayed = 0.0
        self.adelayed = 0.0

        # test decorating the method (doing it functionally for tests)
        ClassMethodTest.decmeth = delayed(delay=delay, sleeper=self.syncsleep)(ClassMethodTest.method)
        assert isinstance(ClassMethodTest.decmeth, wrapt.BoundFunctionWrapper)

        # Instantiation of the class (must be in sync code !)
        ci = ClassMethodTest()

        # calling it as usual as a method
        cc = ci.decmeth(*args, **kwargs)
        assert self.delayed == delay
        assert self.adelayed == 0.0
        resa, reskwa = cc
        assert resa == args
        assert reskwa == kwargs

    #TODO : decorating the class itself ? what semantics ? like decorating __init__ ? like a meta class, smthg else ? *typeclass* ?

class TestAgentTask(unittest.TestCase):

    def test_agenttask(self):
        raise NotImplementedError
        # TODO : HOW ?


