# TODO : full on property testing based on container (category) theory...
import asyncio
import unittest

import aiounittest
from hypothesis import given, infer
from hypothesis import strategies as st

from timecontrol.dcont.dlist import DList


class TestDListState(unittest.TestCase):
    """ Testing DList is a state - BImonad in python """

    # Monad

    @given(element=st.integers())
    def test_return(self, element):
        """ Testing __init__ as 'return' """
        dl = DList([element])  # TODO : type parameter ???

        assert isinstance(dl, DList)
        assert element in dl   # we can check the contents  !  # TODO : same on types ??
        # just to avoid  false positives
        assert element + 42 not in dl
        # TODO: fail tests

    @given(element=st.integers())
    def test_join(self, element):
        """ Testing __init__ as 'join' - function composition as usual """

        ddl = DList(DList([element]))
        dl = DList([element])

        assert ddl == dl
        #TODO: fail tests

    # Comonad

    @given(element=st.integers())
    def test_extract(self, element):
        """ Testing __next__ as 'extract' - iterator protocol """
        dl = DList([element])

        for e in dl:  # using python iterator protocol
            assert e == element  # only one element here !

    @given(element=st.integers())
    def test_duplicate(self, element):
        """ Testing __init__ as 'duplicate' - iterator protocol """

        ddl = DList(DList([element]))
        dl = DList([element])

        assert ddl == dl
        #TODO: fail tests




    # TODO : algebra

