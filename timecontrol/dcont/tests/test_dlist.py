# TODO : full on property testing based on container (category) theory...
import asyncio
import unittest

import aiounittest
from hypothesis import given, infer
from hypothesis import strategies as st

from timecontrol.dcont.dlist import DList, EmptyDList, dlist


class TestDListTime(aiounittest.AsyncTestCase):
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

    @given(arg=st.integers(), result=st.integers())
    def test_comonad_int(self, arg, result):
        """ Testing comonadic interface on DList[int] """

        t = 42
        dl = dlist(t, t)  # monadic return

        assert isinstance(dl, DList)
        assert t in dl  # we can check the contents  !  # TODO : on type instead ??

        # next as comonadic extract
        assert next(dl) == t
        assert next(dl) == t
        assert next(dl) == EmptyDList
        # Note : there is a (affine ?) time semantic of cunsomption here...

        # iter as comonadic duplicate
        assert dl == iter(dl)

        # iterating again starts again (python semantics)
        assert next(dl) == t
        assert next(dl) == t
        assert next(dl) == EmptyDList

        # CAREFUL !
        dld = dlist(dlist(t), dlist(t))

        assert dld != dl

        dle = next(dld)
        assert dle != t
        assert dle == dlist(t)
