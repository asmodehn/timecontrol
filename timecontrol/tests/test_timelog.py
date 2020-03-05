import aiounittest


from hypothesis import given
import hypothesis.strategies as st

from timecontrol.timelog import timelog, TimeLog
from .strats.st_timeinterval import st_timeinterval


class TestTimeLog(aiounittest.AsyncTestCase):

    @given(til=st.lists(elements=st_timeinterval(), max_size=5, unique=True), data=st.data())
    def test_init_monad(self, til, data):
        value_list = data.draw(st.lists(elements=st.integers(min_value=0, max_value=255), min_size= len(til), max_size=len(til)))  # value is not the point here
        # return a -> M a
        tl = timelog(mapping={t: i for t, i in zip(til, value_list)})
        assert isinstance(tl, TimeLog)
        assert len(tl) == len(til), f"len({tl}) != len({til})"

        # join M M a -> M a
        # since we are a bimonad we can be even stronger here
        tlb = timelog(tl)
        assert tlb == tl == tlb  # verifying commutativity of equality

    @given(til=st.lists(elements=st_timeinterval(), max_size=5, unique=True), data=st.data())
    def test_contains_get(self, til, data):
        value_list = data.draw(st.lists(elements=st.integers(min_value=0, max_value=255), min_size= len(til), max_size=len(til)))  # value is not the point here

        tl = timelog(mapping={t: i for t, i in zip(til, value_list)})
        # test that if contained, we can get it, and dual

        dt = data.draw(st.datetimes())

        if dt in tl:
            # make sure we have a directed container = > we get the same type of container
            assert isinstance(tl[dt], TimeLog)

    @given(til=st.lists(elements=st_timeinterval(), max_size=5, unique=True), data=st.data())
    def test_iter_comonad(self, til, data):
        value_list = data.draw(st.lists(elements=st.integers(min_value=0, max_value=255), min_size= len(til), max_size=len(til)))  # value is not the point here
        tl = timelog(mapping={t: i for t, i in zip(til, value_list)})
        # test comonadic that we can iterate on it towards hte past
        # extract M a -> a
        for e in tl:
            isinstance(e, int)

        # duplicate M a -> M M a
        # since we are a bimonad we can be even stronger here
        tlb = timelog(tl)
        # only one level encapsulation
        for e in tl:
            isinstance(e, int)
        # actually equal
        assert tlb == tl == tlb  # verifying commutativity of equality


    # async def test_aiter(self):
    #     # test comonadic that we can iterate on it to the future (and block when needed)
    #     raise NotImplementedError


if __name__ == "__main__":
    import unittest
    unittest.main()
