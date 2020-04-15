import unittest
from typing import List

import st as st
from hypothesis import given, infer
import hypothesis.strategies as st

from timecontrol.typeframe import TypeFrameBase, TypeFrame


class TestTypeFrame(unittest.TestCase):

    def test_0_typeframe_void(self):
        assert issubclass(TypeFrameBase.Void(), TypeFrameBase)
        # Cannot build a value:
        with self.assertRaises(TypeError):
            TypeFrameBase.Void()()
        # TODO : refine proper formal properties to satisfy here...

    @given(values = st.lists(st.integers(), max_size=5))
    def test_1field_typeframe_int(self, values: List[int]):
        LoneValueFrame = TypeFrame("LoneValueFrame", column_types=[("lonevalue", int)])

        f = LoneValueFrame()
        # a lone value frame, empty.
        assert len(f) == 0

        # build static frame from records
        ff = LoneValueFrame(*(LoneValueFrame.Record(v) for v in values))
        assert len(ff) == len(values)

        assert type(f) == type(ff)
        assert f != ff


