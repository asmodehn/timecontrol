import unittest

from timecontrol.utils.proactor import proactor

import asyncio
from collections import abc


# TODO : integrate directly in package with tests
class aenumerate(abc.AsyncIterator):
    """enumerate for async for"""
    def __init__(self, aiterable, start=0):
        self._aiterable = aiterable
        self._i = start - 1

    def __aiter__(self):
        self._ait = self._aiterable.__aiter__()
        return self

    async def __anext__(self):
        # self._ait will raise the apropriate AsyncStopIteration
        val = await self._ait.__anext__()
        self._i += 1
        return self._i, val



class TestProactorGenerator(unittest.TestCase):

    def trigger(self):
        yield 1
        yield 2
        yield 3

    expected_trigger = [1,2,3]

    def proactored(self, **kwargs):
        self.proactored_call = True
        return self.result, kwargs

    def proactored_gen(self, **kwargs):
        self.proactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.iterable_proactor = proactor(trigger=self.trigger())

        self.proactored_call = False

    def test_proactor_function(self):

        proacting = self.iterable_proactor(self.proactored)

        for count, yld in enumerate(proacting):
            assert yld == (self.result, {'proactor_triggered': self.expected_trigger[count]})

    def test_proactor_generator(self):

        proacting = self.iterable_proactor(self.proactored_gen)

        for count, yld in enumerate(proacting):
            assert yld == [
                (self.result, {'proactor_triggered': self.expected_trigger[count]})
            ]  # TODO : maybe an aiostream would be preferred here instead of list ??


class TestAsyncProactorGenerator(unittest.IsolatedAsyncioTestCase):

    def trigger(self):
        yield 1
        yield 2
        yield 3

    expected_trigger = [1,2,3]

    async def async_proactored(self, **kwargs):
        self.proactored_call = True
        return self.result, kwargs

    async def async_proactored_gen(self, **kwargs):
        self.proactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.iterable_proactor = proactor(trigger=self.trigger())

        self.proactored_call = False

    async def test_proactor_function_async(self):

        proacting = self.iterable_proactor(self.async_proactored)

        async for count, yld in aenumerate(proacting):
            assert yld == (self.result, {'proactor_triggered': self.expected_trigger[count]})

    async def test_proactor_generator_async(self):

        proacting = self.iterable_proactor(self.async_proactored_gen)

        async for count, yld in aenumerate(proacting):
            assert yld == [
                (self.result, {'proactor_triggered': self.expected_trigger[count]})
            ]  # TODO : maybe an aiostream would be preferred here instead of list ??


class TestProactorAsyncGenerator(unittest.IsolatedAsyncioTestCase):

    async def trigger(self):
        yield 1
        yield 2
        yield 3

    expected_trigger = [1,2,3]

    def proactored(self, **kwargs):
        self.proactored_call = True
        return self.result, kwargs

    def proactored_gen(self, **kwargs):
        self.proactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.iterable_proactor = proactor(trigger=self.trigger())

        self.proactored_call = False

    async def test_proactor_function(self):

        proacting = self.iterable_proactor(self.proactored)
        # TODO : it can be strange to have hte trigger impact a simple function -> somehow get rid of async here ??
        async for count, yld in aenumerate(proacting):
            assert yld == (self.result, {'proactor_triggered': self.expected_trigger[count]})

    async def test_proactor_generator(self):

        proacting = self.iterable_proactor(self.proactored_gen)

        async for count, yld in aenumerate(proacting):
            assert yld == [
                (self.result, {'proactor_triggered': self.expected_trigger[count]})
            ]  # TODO : maybe an aiostream would be preferred here instead of list ??


class TestAsyncProactorAsyncGenerator(unittest.IsolatedAsyncioTestCase):

    async def trigger(self):
        yield 1
        yield 2
        yield 3

    expected_trigger = [1,2,3]

    async def async_proactored(self, **kwargs):
        self.proactored_call = True
        return self.result, kwargs

    async def async_proactored_gen(self, **kwargs):
        self.proactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.iterable_proactor = proactor(trigger=self.trigger())

        self.proactored_call = False

    async def test_proactor_function_async(self):

        proacting = self.iterable_proactor(self.async_proactored)

        async for count, yld in aenumerate(proacting):
            assert yld == (self.result, {'proactor_triggered': self.expected_trigger[count]})

    async def test_proactor_generator_async(self):

        proacting = self.iterable_proactor(self.async_proactored_gen)

        async for count, yld in aenumerate(proacting):
            assert yld == [
                (self.result, {'proactor_triggered': self.expected_trigger[count]})
            ]  # TODO : maybe an aiostream would be preferred here instead of list ??


if __name__ == '__main__':
    unittest.main()
