import unittest
from datetime import datetime, timedelta, MINYEAR, MAXYEAR

from hypothesis import given
from hypothesis import infer
from hypothesis.strategies import data, timedeltas

from timecontrol.timeslice import TimeSlice


class TestTimeSlice(unittest.TestCase):

    @given(dt1=infer, dt2= infer, data=data())
    def test_interval_algebra(self, dt1:datetime, dt2:datetime, data):
        # we have to plan for timedeltas to avoid overflows
        # Note we limit ourselves to a minimum micro second precision...
        ti1 = TimeSlice(start=dt1, stop=dt1 + data.draw(timedeltas(min_value=timedelta(microseconds=1), max_value=min(dt1 - datetime(year=MINYEAR, month=1, day=1), datetime(year=MAXYEAR, month=12, day=31) - dt1))))
        ti2 = TimeSlice(start=dt2, stop=dt2 + data.draw(timedeltas(min_value=timedelta(microseconds=1), max_value=min(dt2 - datetime(year=MINYEAR, month=1, day=1), datetime(year=MAXYEAR, month=12, day=31) - dt2))))

        def assert_all(t1:TimeSlice, t2:TimeSlice, after:bool = False, before:bool = False, meets:bool = False, overlaps:bool = False, during:bool = False, starts:bool = False, equal:bool = False, finishes:bool = False):
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
        if ti1.stop < ti2.start:
            assert ti1 < ti2 and ti2 > ti1
            assert_all(ti1, ti2, before=True)
        elif ti2.stop < ti1.start:
            assert ti1 > ti2 and ti2 < ti1
            assert_all(ti1, ti2, after=True)
        # meets
        # Note : meets can also be equal if precisions are equals
        elif ti1.stop == ti2.start:
            assert_all(ti1, ti2, meets=True, equal= True)
        elif ti2.stop == ti1.start:
            assert_all(ti2, ti1, meets=True, equal= True)
        # overlaps
        elif ti2.stop > ti1.stop > ti2.start > ti1.start:
            assert_all(ti1, ti2, overlaps=True)
        elif ti1.stop > ti2.stop > ti1.start > ti2.start:
            assert_all(ti2, ti1, overlaps=True)
        # during
        elif ti1.start > ti2.start and ti1.stop < ti2.stop:
            assert ti1 in ti2
            assert_all(ti1, ti2, during=True)
        elif ti2.start > ti1.start and ti2.stop < ti1.stop:
            assert ti2 in ti1
            assert_all(ti2, ti1, during=True)
        # starts or equal
        elif ti2.start == ti1.start:
            if ti2.stop < ti1.stop:
                assert_all(ti2, ti1, starts=True)
            elif ti2.stop == ti1.stop:
                assert ti1 == ti2 and ti2 == ti1
                assert_all(ti1, ti2, equal=True)
            else:
                assert_all(ti1, ti2, starts=True)
        # finishes or equal
        elif ti2.stop == ti1.stop:
            if ti2.start < ti1.start:
                assert_all(ti1, ti2, finishes=True)
            elif ti2.start == ti1.start:
                assert ti1 == ti2  and ti2 == ti1
                assert_all(ti1, ti2, equal=True)
            else:
                assert_all(ti2, ti1, finishes=True)

    def test_as_slice(self):
        raise NotImplementedError


class TestTimeSliceFactory(unittest.TestCase):

    def test_start(self):
        raise NotImplementedError

    def test_stop(self):
        raise NotImplementedError

    def test_step(self):
        raise NotImplementedError
