


import unittest
from datetime import datetime, timedelta, MINYEAR, MAXYEAR

from hypothesis import given
from hypothesis import infer
from hypothesis.strategies import data, timedeltas

from timecontrol.schedules.timeinterval import TimeInterval


class TestTimeInterval(unittest.TestCase):

    @given(dt1=infer, dt2= infer, data=data())
    def test_non_periodic(self, dt1:datetime, dt2:datetime, data):
        # we have to plan for timedeltas to avoid overflows
        ti1 = TimeInterval(datetime=dt1, precision=data.draw(timedeltas(
            min_value=timedelta(), max_value=min(dt1 - datetime(year=MINYEAR, month=1, day=1), datetime(year=MAXYEAR, month=12, day=31) - dt1))))
        ti2 = TimeInterval(datetime=dt2, precision=data.draw(timedeltas(
            min_value=timedelta(), max_value=min(dt2 - datetime(year=MINYEAR, month=1, day=1), datetime(year=MAXYEAR, month=12, day=31) - dt2))))

        def assert_all(t1:TimeInterval, t2:TimeInterval, after:bool = False, before:bool = False, meets:bool = False, overlaps:bool = False, during:bool = False, starts:bool = False, equal:bool = False, finishes:bool = False):
            # before/after
            assert after == t1.after(t2) and after == t2.before(t1)
            assert before == t1.before(t2) and before == t2.after(t1)
            # meets
            assert meets == t1.meets(t2) and meets == t2.meets_inv(t1)
            # overlaps
            assert overlaps == t1.overlaps(t2) and overlaps == t2.overlaps_inv(t1)
            # during
            assert during == t1.during(t2) and during == t2.during_inv(t1)
            # starts
            assert starts == t1.starts(t2) and starts == t2.starts_inv(t1)
            # finishes
            assert finishes == t1.finishes(t2) and finishes == t2.finishes_inv(t1)
            # equal
            assert equal == (t1 == t2) and equal == (t2 == t1)

        # Here we test our implementation of Allen Interval Algebra
        # TODO : add tests to validate we avoid false positives
        # before/after
        if dt1 + ti1.precision/2 < dt2 - ti2.precision/2:
            assert ti1 < ti2 and ti2 > ti1
            assert_all(ti1, ti2, before=True)
        elif dt2 + ti2.precision/2 < dt1 - ti1.precision/2:
            assert ti1 > ti2 and ti2 < ti1
            assert_all(ti1, ti2, after=True)
        # meets
        # Note : meets can also be equal if precision == 0
        elif dt1 + ti1.precision/2 == dt2 - ti2.precision/2:
            assert_all(ti1, ti2, meets=True, equal= ti1.precision == ti2.precision == timedelta())
        elif dt2 + ti2.precision/2 == dt1 - ti1.precision/2:
            assert_all(ti2, ti1, meets=True, equal= ti1.precision == ti2.precision == timedelta())
        # overlaps
        elif dt2 + ti2.precision /2 > dt1 + ti1.precision / 2 > dt2 - ti2.precision / 2 > dt1 - ti1.precision/2:
            assert_all(ti1, ti2, overlaps=True)
        elif dt1 + ti1.precision / 2 > dt2 + ti2.precision / 2 > dt1 - ti1.precision / 2 > dt2 - ti2.precision/2:
            assert_all(ti2, ti1, overlaps=True)
        # during
        elif dt1 - ti1.precision/2 > dt2 - ti2.precision/2 and dt1 + ti1.precision/2 < dt2 + ti2.precision/2:
            assert ti1 in ti2
            assert_all(ti2, ti1, during=True)
        elif dt2 - ti2.precision/2 > dt1 - ti1.precision/2 and dt2 + ti2.precision/2 < dt1 + ti1.precision/2:
            assert ti2 in ti1
            assert_all(ti1, ti2, during=True)
        # starts or equal
        elif dt2 - ti2.precision/2 == dt1 - ti1.precision/2:
            if dt2 + ti2.precision/2 < dt1 + ti1.precision/2:
                assert_all(ti2, ti1, starts=True)
            elif dt2 + ti2.precision/2 == dt1 + ti1.precision/2:
                assert ti1 == ti2 and ti2 == ti1
                assert_all(ti1, ti2, equal=True)
            else:
                assert_all(ti1, ti2, starts=True)
        # finishes or equal
        elif dt2 + ti2.precision/2 == dt1 + ti1.precision/2:
            if dt2 - ti2.precision/2 < dt1 - ti1.precision/2:
                assert_all(ti1, ti2, finishes=True)
            elif dt2 - ti2.precision/2 == dt1 - ti1.precision/2:
                assert ti1 == ti2  and ti2 == ti1
                assert_all(ti1, ti2, equal=True)
            else:
                assert_all(ti2, ti1, finishes=True)

    def test_periodic(self, dt, prec, period):
        raise NotImplementedError


class TestTimeIntervalFactory(unittest.TestCase):

    def test_begin(self):
        raise NotImplementedError

    def test_duration(self):
        raise NotImplementedError

    def test_end(self):
        raise NotImplementedError

    def test_period(self):
        raise NotImplementedError