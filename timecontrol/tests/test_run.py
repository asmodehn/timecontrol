import asyncio

import unittest

from ..run import run


class TestRun(unittest.TestCase):
    def timer(self):
        return self.clock

    def procedure(self):
        self.triggered_call = True
        return self.result

    def procedure_bis(self):
        self.triggered_bis_call = True
        return self.result

    async def coroutine(self):
        self.triggered_call = True
        return self.result

    async def coroutine_bis(self):
        self.triggered_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.triggered_call = False
        self.triggered_bis_call = False

    def test_run_one_procedure(self):
        # run also support passing usual procedures, simply forwarding the result.
        res = run(self.procedure())

        assert self.triggered_call == True
        assert res == self.result

    def test_run_one_coroutine(self):
        coro = self.coroutine()

        # coroutine is like a lazy function
        assert self.triggered_call == False

        # unless you await (in async lazy code)
        # or run() in directed eager code
        res = run(coro)
        assert self.triggered_call == True
        assert res == self.result

    def test_run_two_procedure(self):
        # run also support passing usual procedures, simply forwarding the result.
        res = run(self.procedure(), self.procedure_bis())

        assert self.triggered_call == True
        assert self.triggered_bis_call == True
        assert res == (self.result, self.result)

    def test_run_two_coroutine(self):
        coro = self.coroutine()
        coro_bis = self.coroutine_bis()

        # coroutine is like a lazy function
        assert self.triggered_call == False
        assert self.triggered_bis_call == False

        # unless you await (in async lazy code)
        # or run() in directed eager code
        res = run(coro, coro_bis)
        assert self.triggered_call == True
        assert self.triggered_bis_call == True
        assert res == (self.result, self.result)
