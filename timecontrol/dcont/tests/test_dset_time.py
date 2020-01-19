# TODO : full on property testing based on container (category) theory...
import asyncio
import unittest

import aiounittest
from hypothesis import given, infer
from hypothesis import strategies as st

from timecontrol.dcont.dset import DSet


class TestDSetTime(aiounittest.AsyncTestCase):
    """ Testing DSet is a time - BImonad in python """

    @given(arg=st.integers(), result=st.integers())
    def test_return(self,  arg, result):
        """ Testing __init__ as return """
        async def compute(*args, **kwargs):
            return result

        # can wrap a task (running computation)
        t = compute(arg)  # note : we need to instantiate the task only once (not pure function)
        dl = DSet(t)  # we need to pass REPRESENTATION of computation !

        assert isinstance(dl, DSet)
        assert t in dl   # we can check the contents  !  # TODO : same on types ??
        # just to avoid false positives
        # assert compute(arg+42) not in dl
        #TODO : fail test

    @given(arg=st.integers(), result=st.integers())
    def test_join(self, arg, result):
        """ Testing __init__ as 'join' - function composition as usual """

        async def compute(*args, **kwargs):
            return result

        # can wrap a time-bound computation
        t = compute(arg)  # note : we need to instantiate the task only once (not pure function)
        ddl = DSet(DSet(t))
        dl = DSet(t)

        assert ddl == dl
        #TODO: fail test

    # Comonad

    #@given(arg=st.integers(), result=st.integers())
    async def test_extract(self, arg=42, result=51):
        """ Testing await as 'extract' - async protocol  -> getting result <~> extracting from timebox """

        # Hypothesis not usable directly (until we move to trio async via extension)

        async def compute(*args, **kwargs):
            return result

        t = compute(arg)
        dl = DSet(t)

        assert await dl() == DSet(result)

    @given(arg=st.integers(), result=st.integers())
    def test_duplicate(self, arg, result):
        """ Testing async call as 'duplicate' - async protocol -> scheduling/timeboxing the timeboxed computation """

        async def compute(*args, **kwargs):
            return result

        t = compute(arg)
        dl = DSet([t])

        dt = dl()
        dtt = dl()()
        # calling the list is the same as putting it into itself...
        assert dt == DSet(dl)

        # TODO: fail tests
