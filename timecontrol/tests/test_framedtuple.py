import inspect
import unittest
from typing import List, Tuple, Type, NamedTuple

import static_frame as sf
import typing
from hypothesis import given, infer, Verbosity, settings
import hypothesis.strategies as st

from timecontrol.tests.strats.st_framedtuple import st_FramedTuple, identifier_strategy, typehints_strategy
from timecontrol.framedtuple import FramedTupleMeta, EmptyFrameTuple, UnitFramedTupleMeta


class TestFramedTuple(unittest.TestCase):

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), ft=st_FramedTuple())
    def test_framedtuple_instance_equality(self, data, ft):

        if ft is not EmptyFrameTuple:  # TODO : strategy param to avoid generating this ?

            ta = data.draw(ft._strategy)

            tb = data.draw(ft._strategy)

            assert (ta == tb) == (ta._field_types == tb._field_types and all(tuple(getattr(ta, f) == getattr(tb, f) for f in ta._fields)))

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), fta=st_FramedTuple(), ftb=st_FramedTuple())
    def test_framedtuple_equality(self, data, fta, ftb):

        assert (fta == ftb) == (
                fta == ftb == EmptyFrameTuple or (
                    fta.__name__ == ftb.__name__ and fta._column_types == ftb._column_types
        ))

        # extensional equality is not intensional (careful with empty type)
        assert (fta == ftb == EmptyFrameTuple) or (not fta is ftb)

        # copy is just by reference -> intensionally equal
        ftc = fta
        assert ftc is fta

        if fta is not EmptyFrameTuple and ftb is not EmptyFrameTuple:
            # instance equality implies type equality ! (more strict than usual python)
            ta = data.draw(fta._strategy)
            tb = data.draw(ftb._strategy)
            if ta == tb:
                assert fta == ftb

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), ft=st_FramedTuple())
    def test_framedtuple_instance_iterator(self, data, ft):

        if ft is not EmptyFrameTuple:
            ta = data.draw(ft._strategy)

            # tuples are iterable as usual
            for n, v in ta._asdict().items():
                assert n in ta._fields
                assert type(v) is ta._field_types[n]

    @settings(verbosity=Verbosity.verbose)
    @given(data=st.data(), fta=st_FramedTuple())
    def test_framedtuple_iterator(self, data, fta):

        if fta is not EmptyFrameTuple:  # TODO : strategy param to avoid generating this ?

            if not isinstance(fta, UnitFramedTupleMeta):  # Unit Types already have their value instantiated...
                with self.assertRaises(StopIteration) as si:
                    next(iter(fta))

            ta = data.draw(fta._strategy)

            # type iterate on created tuple instances
            for t in fta:
                assert type(t) is type(ta) is fta  # the framedtuple is the type
                assert isinstance(t, fta) and isinstance(t, tuple)


    # @settings(verbosity=Verbosity.verbose)
    # @given(data=st.data(), ft=st_FramedTuple())
    # def test_framedtuple_instance_indexer(self, data, ft):
    #     ta = data.draw(ft._strategy)
    #
    #     tb = data.draw(ft._strategy)
    #
    #     # fields are the index and point to a value in the specified type
    #     assert all(type(ta[f]) is type(tb[f]) is t for f, t in ta._column_types)
    #
    # @settings(verbosity=Verbosity.verbose)
    # @given(data=st.data(), fta=st_FramedTuple(), ftb=st_FramedTuple())
    # def test_framedtuple_indexer(self, data, fta, ftb):
    #
    #     # columns are the index and point to the type of that column
    #     assert all(fta[c] is ftb[c] is t for c, t in fta._column_types)


if __name__ == '__main__':
    unittest.main()