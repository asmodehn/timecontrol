import unittest
from datetime import datetime, timedelta, MINYEAR, MAXYEAR

from hypothesis import given
from hypothesis import infer
from hypothesis.strategies import data, timedeltas, datetimes

from timecontrol.timeinterval import TimeInterval


class TestTimeInterval(unittest.TestCase):

    def assert_all(self, t1: TimeInterval, t2: TimeInterval, after: bool = False, before: bool = False, meets: bool = False,
                   overlaps: bool = False, during: bool = False, starts: bool = False, equal: bool = False,
                   finishes: bool = False):
        # before/after
        assert after == t1.after(t2) and after == t2.before(t1), f"{t1} after {t2} and {t2} before {t1}"
        assert before == t1.before(t2) and before == t2.after(t1), f"{t1} before {t2} and {t2} after {t1}"
        # meets
        assert meets == t1.meets(t2) and meets == t2.meets_inv(t1),f"{t1} meets {t2} and {t2} meets_inv {t1}"
        # overlaps
        assert overlaps == t1.overlaps(t2) and overlaps == t2.overlaps_inv(t1), f"{t1} overlaps {t2} and {t2} overlaps_inv {t1}"
        # during
        assert during == t1.during(t2) and during == t2.during_inv(t1), f"{t1} during {t2} and {t2} during_inv {t1}"
        # starts
        assert starts == t1.starts(t2) and starts == t2.starts_inv(t1), f"{t1} starts {t2} and {t2} start_inv {t1}"
        # finishes
        assert finishes == t1.finishes(t2) and finishes == t2.finishes_inv(t1), f"{t1} finishes {t2} and {t2} finishes_inv {t1}"
        # equal
        assert equal == (t1 == t2) and equal == (t2 == t1), f"{t1} equals {t2} and {t2} equals {t1}"

    @given(dt1=infer, data=data())
    def test_interval_before(self, dt1:datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt1, stop=dt2)
        ti2 = TimeInterval(start=dt3, stop=dt4)

        assert ti1 < ti2 and ti2 > ti1
        self.assert_all(ti1, ti2, before=True)

    @given(dt1=infer, data=data())
    def test_interval_after(self, dt1:datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt3, stop=dt4)
        ti2 = TimeInterval(start=dt1, stop=dt2)

        assert ti1 > ti2 and ti2 < ti1
        self.assert_all(ti1, ti2, after=True)

    @given(dt1=infer, data=data())
    def test_interval_meets(self, dt1: datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = dt2
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt1, stop=dt2)
        ti2 = TimeInterval(start=dt3, stop=dt4)

        self.assert_all(ti1, ti2, meets=True)

    @given(dt1=infer, data=data())
    def test_interval_overlaps(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt1, stop=dt3)
        ti2 = TimeInterval(start=dt2, stop=dt4)

        self.assert_all(ti1, ti2, overlaps=True)

    @given(dt1=infer, data=data())
    def test_interval_during(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt2, stop=dt3)
        ti2 = TimeInterval(start=dt1, stop=dt4)

        assert ti1 in ti2
        self.assert_all(ti1, ti2, during=True)

    @given(dt1=infer, data=data())
    def test_interval_starts(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt1, stop=dt2)
        ti2 = TimeInterval(start=dt1, stop=dt3)

        self.assert_all(ti1, ti2, starts=True)

    @given(dt1=infer, data=data())
    def test_interval_finishes(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt2, stop=dt3)
        ti2 = TimeInterval(start=dt1, stop=dt3)

        self.assert_all(ti1, ti2, finishes=True)

    @given(dt1=infer, data=data())
    def test_interval_equals(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))

        ti1 = TimeInterval(start=dt1, stop=dt2)
        ti2 = TimeInterval(start=dt1, stop=dt2)

        assert ti1 == ti2
        self.assert_all(ti1, ti2, equal=True)


class TestTimeIntervalFactory(unittest.TestCase):

    def test_start(self):
        raise NotImplementedError

    def test_stop(self):
        raise NotImplementedError
