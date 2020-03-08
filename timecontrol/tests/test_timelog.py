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

        dt = data.draw(st.integers(min_value=tl.begin, max_value=tl.end))

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

    def test_call_comonad(self):
        # TODO : actual properties to test here ?
        # a drivable clock for testing
        test_clock = 0

        def clock():
            return test_clock

        tl = timelog(mapping=dict(), timer_ns = clock, timeframe_ns=10)

        # test comonadic that we can iterate on it towards the future
        # extract M a -> a

        acc = tl()

        # starting generator
        curti, initv = acc.send(None)
        assert initv == 0
        assert curti.start == test_clock and curti.stop == test_clock + tl.timeframe_ns

        curti1, initv1 = acc.send(42)
        assert curti == curti1
        assert initv1 == 42

        test_clock += 5

        curti2, initv2 = acc.send(42)
        assert curti == curti2 == curti1
        assert initv2 == 84

        test_clock += 6  # going over the timeframe

        with self.assertRaises(StopIteration) as exc_ctx:
            acc.send(51)

        assert exc_ctx.exception

        # keep going
        acc_again = tl()

        # starting generator
        curti_again, initv_again = acc_again.send(None)
        assert initv_again == 0
        assert curti_again.start == test_clock and curti_again.stop == test_clock + tl.timeframe_ns


    # we do not depend on hypothesis here, as this can be quite complex and take some time
    # def test_aiter_comonad(self):
    #     import asyncio
    #     import random
    #
    #     # a drivable clock for testing
    #     test_clock = 0
    #
    #     def clock():
    #         return test_clock
    #
    #     tl = timelog(mapping=dict(), timer_ns = clock)
    #
    #     # test comonadic that we can iterate on it towards the future
    #     # extract M a -> a
    #
    #     inserted = []
    #     extracted = []
    #
    #     async def putin(drives: bool = False):
    #         nonlocal test_clock, inserted
    #         tf = tl()  # generator
    #         while tf:
    #             nextv = random.randint(1, 42)
    #             inserted.append(nextv)
    #             tf.send(nextv)  # sink
    #             if drives:  # one tick in one loop, to prevent compressing values
    #                 test_clock += tl.timeframe_ns
    #
    #     async def getout(drives: bool = False):
    #         nonlocal test_clock, extracted
    #         async for v in tl:  # source
    #             assert isinstance(v, int)
    #             extracted.append(v)
    #             if drives:  # one tick in one loop, to prevent accumulating values
    #                 test_clock += tl.timeframe_ns
    #
    #     async def sched_pull(loop):
    #         put = loop.create_task(putin())
    #         get = loop.create_task(getout(True))
    #
    #         await asyncio.sleep(10)
    #         put.cancel()
    #         get.cancel()
    #
    #     async def sched_push(loop):
    #         put = loop.create_task(putin(True))
    #         get = loop.create_task(getout())
    #
    #         await asyncio.sleep(10)
    #         get.cancel()
    #         put.cancel()
    #
    #     loop = asyncio.get_event_loop()
    #     asyncio.run(sched_pull(loop))
    #
    #     assert inserted
    #     assert extracted
    #     assert inserted == extracted, f"{inserted} => {extracted}"
    #
    #     # reset
    #     inserted.clear()
    #     extracted.clear()
    #
    #     asyncio.run(sched_push(loop))
    #
    #     assert inserted
    #     assert extracted
    #     assert inserted == extracted, f"{inserted} => {extracted}"
    #
    #     # duplicate M a -> M M a
    #     # since we are a bimonad we can be even stronger here
    #     tlb = timelog(tl)
    #
    #     # actually equal
    #     assert tlb == tl == tlb  # verifying commutativity of equality


if __name__ == "__main__":
    import unittest
    unittest.main()
