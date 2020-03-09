import unittest
from datetime import datetime, timedelta, MINYEAR, MAXYEAR

import typing
from hypothesis import given
from hypothesis import infer
from hypothesis.strategies import data, timedeltas, datetimes

from timecontrol.datetimeinterval import DateTimeInterval


class TestDateTimeInterval(unittest.TestCase):

    def assert_all(self, t1: typing.Union[datetime, DateTimeInterval], t2: typing.Union[datetime, DateTimeInterval],
                   after: bool = False, before: bool = False, meets: bool = False,
                   overlaps: bool = False, during: bool = False, starts: bool = False, equal: bool = False,
                   finishes: bool = False):

        # before/after
        if isinstance(t1, DateTimeInterval):
            assert after == t1.after(t2), f"{t1} after {t2}"
            assert before == t1.before(t2), f"{t1} before {t2}"
        else:
            assert after == (t1 > t2), f"{t1} > {t2}"
            assert before == (t1 < t2), f"{t1} < {t2}"
        if isinstance(t2, DateTimeInterval):
            assert after == t2.before(t1), f"{t2} before {t1}"
            assert before == t2.after(t1), f"{t2} after {t1}"
        else:
            assert after == (t2 < t1), f"{t2} < {t1}"
            assert before == (t2 > t1), f"{t2} > {t1}"

        # meets
        if isinstance(t1, DateTimeInterval):
            assert meets == t1.meets(t2), f"{t1} meets {t2}"
        else:
            assert meets == (t1 == t2.start), f"{t1} == {t2.start} bound of {t2}"
        if isinstance(t2, DateTimeInterval):
            assert meets == t2.meets_inv(t1), f"{t2} meets_inv {t1}"
        else:
            assert meets == (t2 == t1.stop), f"{t2} == {t1.stop} bound of {t1}"

        # overlaps
        if isinstance(t1, DateTimeInterval):
            assert overlaps == t1.overlaps(t2), f"{t1} overlaps {t2}"
        if isinstance(t2, DateTimeInterval):
            assert overlaps == t2.overlaps_inv(t1), f"{t2} overlaps_inv {t1}"
        if overlaps and (isinstance(t1, int) or isinstance(t2, int)):
            raise RuntimeError(" This is not applicable to ints !")

        # during
        if isinstance(t1, DateTimeInterval):
            assert during == t1.during(t2), f"{t1} during {t2}"
        else:
            assert during == (t1 in t2), f"{t1} in {t2}"  # fallback on contains

        if isinstance(t2, DateTimeInterval):
            assert during == t2.during_inv(t1), f"{t2} during_inv {t1}"
        else:
            assert during == t1.during(t2), f"{t1} during {t2}"  # fallback on inverse relation (symmetric)

        # starts
        if isinstance(t1, DateTimeInterval):
            assert starts == t1.starts(t2), f"{t1} starts {t2}"
        else:
            assert starts == (t1 == t2.start), f"{t1} == {t2.start}"

        if isinstance(t2, DateTimeInterval):
            assert starts == t2.starts_inv(t1), f"{t2} start_inv {t1}"
        else:
            assert starts == (t1 == t2)  # fallback on equality TODO : WHAT ELSE ???

        # finishes
        if isinstance(t1, DateTimeInterval):
            assert finishes == t1.finishes(t2), f"{t1} finishes {t2}"
        else:
            assert finishes == (t1 == t2.stop)

        if isinstance(t2, DateTimeInterval):
            assert finishes == t2.finishes_inv(t1), f"{t2} finishes_inv {t1}"
        else:
            assert finishes == (t1 == t2)  # fallback on equality TODO : WHAT ELSE ???

        # equal
        # same for interval or ints
        assert equal == (t1 == t2) and equal == (t2 == t1), f"{t1} equals {t2} and {t2} equals {t1}"

    @given(dt1=infer, data=data())
    def test_interval_before(self, dt1:datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt2)
        ti2 = DateTimeInterval(start=dt3, stop=dt4)

        assert ti1 < ti2 and ti2 > ti1
        self.assert_all(ti1, ti2, before=True)

    @given(dt1=infer, data=data())
    def test_interval_before_datetime(self, dt1:datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt2)

        assert ti1 < dt3 and dt3 > ti1
        self.assert_all(ti1, dt3, before=True)

    @given(dt1=infer, data=data())
    def test_interval_after(self, dt1:datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt3, stop=dt4)
        ti2 = DateTimeInterval(start=dt1, stop=dt2)

        assert ti1 > ti2 and ti2 < ti1
        self.assert_all(ti1, ti2, after=True)

    @given(dt1=infer, data=data())
    def test_interval_meets(self, dt1: datetime, data):

        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = dt2
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt2)
        ti2 = DateTimeInterval(start=dt3, stop=dt4)

        self.assert_all(ti1, ti2, meets=True)

    @given(dt1=infer, data=data())
    def test_interval_overlaps(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt3)
        ti2 = DateTimeInterval(start=dt2, stop=dt4)

        self.assert_all(ti1, ti2, overlaps=True)

    @given(dt1=infer, data=data())
    def test_interval_during(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))
        dt4 = data.draw(datetimes(min_value=dt3 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt2, stop=dt3)
        ti2 = DateTimeInterval(start=dt1, stop=dt4)

        assert ti1 in ti2
        self.assert_all(ti1, ti2, during=True)

    @given(dt1=infer, data=data())
    def test_interval_starts(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt2)
        ti2 = DateTimeInterval(start=dt1, stop=dt3)

        self.assert_all(ti1, ti2, starts=True)

    @given(dt1=infer, data=data())
    def test_interval_finishes(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))
        dt3 = data.draw(datetimes(min_value=dt2 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt2, stop=dt3)
        ti2 = DateTimeInterval(start=dt1, stop=dt3)

        self.assert_all(ti1, ti2, finishes=True)

    @given(dt1=infer, data=data())
    def test_interval_equals(self, dt1: datetime, data):
        # generating other datetimes, preventing equality
        dt2 = data.draw(datetimes(min_value=dt1 + timedelta(microseconds=1)))

        ti1 = DateTimeInterval(start=dt1, stop=dt2)
        ti2 = DateTimeInterval(start=dt1, stop=dt2)

        assert ti1 == ti2
        self.assert_all(ti1, ti2, equal=True)


class TestDateTimeIntervalFactory(unittest.TestCase):

    def test_invertedbounds(self):
        raise NotImplementedError

    def test_start(self):
        raise NotImplementedError

    def test_stop(self):
        raise NotImplementedError
