import unittest

from ..callscheduler import callscheduler


class TestCallLimiter(unittest.TestCase):
    def timer(self):
        return self.clock

    def sleepcounter(self, to_sleep):
        if to_sleep >0:
            self.slept = to_sleep
        else:
            self.slept = 0

    def scheduled(self):
        self.scheduled_call = True
        return self.result

    def scheduled_bis(self):
        self.scheduled_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        # We build a limiter based on a local test clock
        self.scheduler = callscheduler(ratelimit=5, timer=self.timer, sleeper=self.sleepcounter)

        self.scheduled_call = False
        self.scheduled_bis_call = False

    def test1_one_notscheduled(self):
        assert self.clock == 0
        self.clock = 3

        scheduled = self.scheduler(self.scheduled)

        next(scheduled())
        assert self.slept == 2
        assert self.scheduled_call == True

    def test1_one_scheduled(self):
        assert self.clock == 0
        self.clock = 7

        scheduled = self.scheduler(self.scheduled)

        next(scheduled())
        assert self.slept == 0
        assert self.scheduled_call == True


class TestASyncCallLimiter(unittest.IsolatedAsyncioTestCase):
    def timer(self):
        return self.clock

    async def sleepcounter(self, to_sleep):
        if to_sleep >0:
            self.slept = to_sleep
        else:
            self.slept = 0

    async def scheduled_coro(self):
        self.scheduled_call = True
        return self.result

    async def scheduled_bis_coro(self):
        self.scheduled_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        # We build a limiter based on a local test clock
        self.scheduler = callscheduler(ratelimit=5, timer=self.timer, sleeper=self.sleepcounter)

        self.scheduled_call = False
        self.scheduled_bis_call = False

    async def test1_one_notscheduled_coro(self):
        assert self.clock == 0
        self.clock = 3

        scheduled = self.scheduler(self.scheduled_coro)

        async for c in scheduled():
            assert self.slept == 2
            assert self.scheduled_call == True
            break

    async def test1_one_scheduled_coro(self):
        assert self.clock == 0
        self.clock = 7

        scheduled = self.scheduler(self.scheduled_coro)

        async for c in scheduled():
            assert self.slept == 0
            assert self.scheduled_call == True
            break