import asyncio
import unittest

import aiounittest
from hypothesis import given, infer
from hypothesis import strategies as st

from timecontrol.dcont.dlist import DList, EmptyDList, dlist



class TestDListTime(unittest.TestCase):
    """ Testing DList is a time - BImonad in python """

    @given(arg=st.integers(), result=st.integers())
    def test_monad_int(self,  arg, result):
        """ Testing monadic interface on DList[int] """

        t = 42
        dl = dlist(t, t)   # monadic return

        assert isinstance(dl, DList)
        assert t in dl   # we can check the contents  !  # TODO : on type instead ??

        # implicit monadic join
        ddl = dlist(dlist(t, t))

        assert ddl == dl

        # CAREFUL !
        dld = dlist(dlist(t), dlist(t))

        assert dld != dl

    @given(st.data())
    def test_comonad_int(self, data):
        """ Testing comonadic interface on DList[int] """

        t = data.draw(st.integers())
        dl = dlist(t, t)  # monadic return

        assert isinstance(dl, DList)
        assert t in dl  # we can check the contents  !  # TODO : on type instead ??

        # next as getting subtype , via the comonadic extract in TIME.
        # It is not the one in STATE - getitem - and uses different types because of container time semantics.
        assert next(dl) == dlist(t)
        assert next(dl) == dlist(t)
        # we can go on for ever but
        assert next(next(dl)) == EmptyDList
        # Note : there is a (affine ?) time semantic of cunsomption here in one line, but not in sequential call...

        # CAREFUL with monadic join, it doesnt alter structure !
        dld = dlist(dlist(t), dlist(t))
        assert dld != dl

        dln = next(dld)
        assert dln != t
        assert dln == dlist(t)
