import asyncio
import inspect
import unittest

# The five types of functions in python, for test
import typing
import wrapt
from hypothesis import given, infer
import hypothesis.strategies as st

from timecontrol.agenttask import fun2coro


def function_test(*args, **kwargs):
    return args, kwargs


async def coroutine_test(*args, **kwargs):
    return args, kwargs


def generator_test(*args, **kwargs):
    for a in (args, kwargs):
        yield a
    return args, kwargs


async def async_generator_test(*args, **kwargs):
    for a in (args, kwargs):
        yield a
    return


# Notice : This is a Coroutine watching a generator, and returning what was yielded
async def generator_watcher(watched: typing.Coroutine, *args, **kwargs):
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
        ret_args, ret_kwargs = si
        assert ret_args == res_args
        assert ret_kwargs== res_kwargs
    finally:
        return res_args, res_kwargs


# Notice : This is a Coroutine watching an async generator, and returning what was yielded
async def async_generator_watcher(watched: typing.Coroutine, *args, **kwargs):
    gen = watched
    res_args = await gen.asend(None)
    assert res_args == args
    res_kwargs = await gen.asend(None)
    assert res_kwargs == kwargs
    # return has to be None (py3.7)
    return res_args, res_kwargs


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
        resa, reskwa = asyncio.run(generator_watcher(cc, *args, **kwargs))
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

    def test_delayed(self):
        raise NotImplementedError
        # TODO : HOW ?


class TestAgentTask(unittest.TestCase):

    def test_agenttask(self):
        raise NotImplementedError
        # TODO : HOW ?
