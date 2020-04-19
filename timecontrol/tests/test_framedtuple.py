import inspect
import unittest
from typing import List, Tuple, Type, NamedTuple

import static_frame as sf
import typing
from hypothesis import given, infer, Verbosity, settings
import hypothesis.strategies as st

from timecontrol.tests.strats.st_framedtuple import st_FramedTuple, identifier_strategy, typehints_strategy
from timecontrol.framedtuple import FramedTupleMeta


class TestFramedTuple(unittest.TestCase):

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), ft=st_FramedTuple())
    def test_framedtuple_instance_equality(self, data, ft):
        ta = data.draw(ft._strategy)

        tb = data.draw(ft._strategy)

        assert (ta == tb) == (ta._field_types == tb._field_types and all(tuple(getattr(ta, f) == getattr(tb, f) for f in ta._fields)))

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), fta=st_FramedTuple(), ftb=st_FramedTuple())
    def test_framedtuple_equality(self, data, fta, ftb):

        assert (fta == ftb) == (fta.__name__ == ftb.__name__ and fta._column_types == ftb._column_types)

        # extensional equality is not intensional
        assert not fta is ftb

        # copy is just by reference -> intensionally equal
        ftc = fta
        assert ftc is fta

        # instance equality implies type equality ! (more strict than usual python)
        ta = data.draw(fta._strategy)
        tb = data.draw(ftb._strategy)
        if ta == tb:
            assert fta == ftb





if __name__ == '__main__':
    unittest.main()