


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

        # Here we test our implementation of Allen Interval Algebra
        # TODO : add tests to validate we avoid false positives
        # before/after
        if dt1 + ti1.precision/2 < dt2 - ti2.precision/2:
            assert ti1 < ti2 and ti2 > ti1
        elif dt2 + ti2.precision/2 < dt1 - ti1.precision/2:
            assert ti2 < ti1 and ti1 > ti2
        # meets
        elif dt1 + ti1.precision/2 == dt2 + ti2.precision/2:
            assert ti1.meets(ti2) and ti2.meets_inv(ti1)
        elif dt2 + ti2.precision/2 == dt1 - ti1.precision/2:
            assert ti2.meets(ti1) and ti1.meets_inv(ti2)
        # overlaps
        elif dt1 + ti1.precision / 2 > dt2 + ti2.precision / 2:
            assert ti1.overlaps(ti2) and ti2.overlaps_inv(ti1)
        elif dt2 + ti2.precision / 2 > dt1 - ti1.precision / 2:
            assert ti2.overlaps(ti1) and ti1.overlaps_inv(ti2)
        # during
        elif dt1 - ti1.precision/2 > dt2 - ti2.precision/2 and dt1 + ti1.precision/2 < dt2 + ti2.precision/2:
            assert ti1 in ti2 and ti2.during(ti1) and ti1.during_inv(ti2)
        elif dt2 - ti2.precision/2 > dt1 - ti1.precision/2 and dt2 + ti2.precision/2 < dt1 + ti1.precision/2:
            assert ti2 in ti1 and ti1.during(ti2) and ti2.during_inv(ti1)
        # starts or equal
        elif dt2 - ti2.precision/2 == dt1 - ti1.precision/2:
            if dt2 + ti2.precision/2 < dt1 + ti1.precision/2:
                assert ti2.starts(ti1) and ti1.starts_inv(ti2)
            elif dt2 + ti2.precision/2 == dt1 + ti1.precision/2:
                assert ti1 == ti2 and ti2 == ti1
            else:
                assert ti1.starts(ti2) and ti2.starts_inv(ti1)
        # finishes or equal
        elif dt2 + ti2.precision/2 == dt1 + ti1.precision/2:
            if dt2 - ti2.precision/2 < dt1 - ti1.precision/2:
                assert ti1.finishes(ti2) and ti2.finishes_inv(ti1)
            elif dt2 - ti2.precision/2 == dt1 - ti1.precision/2:
                assert ti1 == ti2  and ti2 == ti1
            else:
                assert ti2.finishes(ti1) and ti1.finishes_inv(ti2)

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