# TODO : full on property testing based on container (category) theory...
import asyncio
import unittest

import aiounittest
from hypothesis import given, infer
from hypothesis import strategies as st

from timecontrol.dcont.ddict import DDict, EmptyDDict, ddict


class TestDDictTime(aiounittest.AsyncTestCase):
    """ Testing DList is a time - BImonad in python """

    @given(arg=st.integers(), result=st.integers())
    def test_monad_int(self,  arg, result):
        """ Testing monadic interface on DList[int] """

        t = 42
        r, dd = ddict(answer1=t, answer2=t)   # monadic return

        assert r == ">"  # root of ddict

        assert isinstance(dd, DDict)
        assert t in dd   # we can check the contents  !  # TODO : on type instead ??

        # implicit monadic join
        ddd = ddict(embedded=ddict(answer1=t, answer2=t))

        assert ddd == dd  # As if we were moving focus, here 'embedded' completely disappears !

        # CAREFUL ! Here embedded stays !
        dddd = ddict(embedded1=ddict(answer=t), embedded2=ddict(answer=t))

        assert dddd != dd

    @given(arg=st.integers(), result=st.integers())
    def test_comonad_int(self, arg, result):
        """ Testing comonadic interface on DList[int] """

        t = 42
        dt = ddict(sub1=t)
        dd = ddict(answer1=dt, answer2=ddict(sub2=t))   # monadic return

        assert isinstance(dd, DDict)
        assert t in dt
        assert dt in dd  # we can check the contents  !  # TODO : on type instead ??
        assert not t in dd  # but only at first level (some laziness here...)

        # next as getting subtype , via the comonadic extract in TIME.
        # It is not the one in STATE - getitem - and uses different types because of container time semantics.
        assert next(dd) in [dt, ddict(path='>answer2', sub2=t)]  # indeterminism !
        assert next(dd) in [dt, ddict(sub2=t)]  # indeterminism !
        # we can go on for ever but
        assert next(next(dd)) in [ddict(**{'>answer1;sub1': EmptyDDict}), ddict(**{'>answer2;sub2': EmptyDDict})]
        # Note : there is a (affine ?) time semantic of cunsomption here in one line, but not in sequential call...

        # CAREFUL with monadic join, it doesnt alter structure !
        ddd = ddict(elm1=ddict(answer=t), elm2=ddict(answer=t))
        assert ddd != dd
