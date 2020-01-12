import unittest

from ..overlimiter import OverLimiter, OverTimeLimit


class TestOverLimiter(unittest.TestCase):
    def timer(self, incr=0):
        return self.clock

    def limited(self):
        self.limited_call = True
        return self.result

    def limited_bis(self):
        self.limited_bis_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        # TODO : have some  <1 variations, to simulate small time measurement problems on machines,
        #        and test we are not sensitive to it ?
        self.result = 42

        # We build a limiter based on a local test clock
        self.limiter = OverLimiter(period=5, timer=self.timer)

        self.limited_call = False
        self.limited_bis_call = False

    def test1_one_overlimit(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)
        with self.assertRaises(OverTimeLimit) as otl:
            limited()
        assert otl.exception.elapsed == self.clock
        assert otl.exception.expected == self.limiter.period
        assert otl.exception.result == self.result
        assert self.limited_call == True

    def test1_one_underlimit(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited)

        limited()
        assert self.limited_call == True

    def test2_multi_overlimit(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        with self.assertRaises(OverTimeLimit) as otl:
            limited()
        assert otl.exception.elapsed == self.clock
        assert otl.exception.expected == self.limiter.period
        assert otl.exception.result == self.result
        assert self.limited_call == True

        self.clock += 7

        with self.assertRaises(OverTimeLimit) as otl:
            limited_bis()
        assert otl.exception.elapsed == 7
        assert otl.exception.expected == self.limiter.period
        assert otl.exception.result == self.result
        assert self.limited_bis_call == True

    def test2_multi_underlimit(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        limited()
        assert self.limited_call == True

        self.clock += 1  # note : if we get over period we will pass since previous was not called.

        limited_bis()
        assert self.limited_bis_call == True

    def test3_multi_overunder(self):
        assert self.clock == 0
        self.clock = 7

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        with self.assertRaises(OverTimeLimit) as otl:
            limited()
        assert otl.exception.elapsed == self.clock
        assert otl.exception.expected == self.limiter.period
        assert otl.exception.result == self.result
        assert self.limited_call == True

        self.clock += 3

        limited_bis()
        assert self.limited_bis_call == True

    def test3_multi_underover(self):
        assert self.clock == 0
        self.clock = 3

        limited = self.limiter(self.limited)
        limited_bis = self.limiter(self.limited_bis)

        limited()
        assert self.limited_call == True

        self.clock += 7

        with self.assertRaises(OverTimeLimit) as otl:
            limited_bis()
        assert otl.exception.elapsed == 7
        assert otl.exception.expected == self.limiter.period
        assert otl.exception.result == self.result
        assert self.limited_bis_call == True
