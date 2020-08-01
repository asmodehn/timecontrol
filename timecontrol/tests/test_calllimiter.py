import unittest

from ..calllimiter import calllimiter


class TestCallLimiter(unittest.TestCase):
    def timer(self):
        return self.clock

    def sleepcounter(self, to_sleep):
        self.slept = to_sleep

    def limited(self):
        self.limited_call = True
        return self.result

    def limited_bis(self):
        self.limited_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        # We build a limiter based on a local test clock
        self.limiter = calllimiter(ratelimit=5, timer=self.timer, sleeper=self.sleepcounter)

        self.limited_call = False
        self.limited_bis_call = False

    def test1_one_notlimited(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)

        limited()
        assert self.slept == 0
        assert self.limited_call == True

    def test1_one_limited(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited)

        limited()
        assert self.slept == 2
        assert self.limited_call == True

    def test2_multi_notlimited(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 7

        limited_bis()
        assert self.slept == 0
        assert self.limited_bis_call == True

    def test2_multi_limited(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        limited()
        assert self.slept == 2
        assert self.limited_call == True

        self.clock += 1  # note : if we get over period we will pass since previous was not called.

        limited_bis()
        assert self.slept == 4
        assert self.limited_bis_call == True

    def test3_multi_alternate(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 3

        limited_bis()
        assert self.slept == 2
        assert self.limited_bis_call == True

        assert self.clock == 10
        self.clock += 6

        # reset slept counter
        self.slept = 0

        limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 3

        limited_bis()
        assert self.slept == 2
        assert self.limited_bis_call == True


class TestASyncCallLimiter(unittest.IsolatedAsyncioTestCase):
    def timer(self):
        return self.clock

    async def sleepcounter(self, to_sleep):
        # TODO : admit a sleeper that can be both sync or async ??
        self.slept = to_sleep

    async def limited_coro(self):
        self.limited_call = True
        return self.result

    async def limited_bis_coro(self):
        self.limited_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        # We build a limiter based on a local test clock
        self.limiter = calllimiter(ratelimit=5, timer=self.timer, sleeper=self.sleepcounter)

        self.limited_call = False
        self.limited_bis_call = False

    async def test1_one_notlimited_coro(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited_coro)

        await limited()
        assert self.slept == 0
        assert self.limited_call == True

    async def test1_one_limited_coro(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited_coro)

        await limited()
        assert self.slept == 2
        assert self.limited_call == True

    async def test2_multi_notlimited_coro(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited_coro)
        limited_bis = self.limiter(self.limited_bis_coro)

        await limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 7

        await limited_bis()
        assert self.slept == 0
        assert self.limited_bis_call == True

    async def test2_multi_limited_coro(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited_coro)
        limited_bis = self.limiter(self.limited_bis_coro)

        await limited()
        assert self.slept == 2
        assert self.limited_call == True

        self.clock += 1  # note : if we get over period we will pass since previous was not called.

        await limited_bis()
        assert self.slept == 4
        assert self.limited_bis_call == True

    async def test3_multi_overunder_coro(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited_coro)
        limited_bis = self.limiter(self.limited_bis_coro)

        await limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 3

        await limited_bis()
        assert self.slept == 2
        assert self.limited_bis_call == True

        assert self.clock == 10
        self.clock += 6

        # reset slept counter
        self.slept = 0

        await limited()
        assert self.slept == 0
        assert self.limited_call == True

        self.clock += 3

        await limited_bis()
        assert self.slept == 2
        assert self.limited_bis_call == True