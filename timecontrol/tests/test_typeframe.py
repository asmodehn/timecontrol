import inspect
import unittest
from typing import List, Tuple, Type, NamedTuple

import static_frame as sf
import typing
from hypothesis import given, infer
import hypothesis.strategies as st

from timecontrol.tests.strats.st_typeframe import st_TypeFrame
from timecontrol.typeframe import EmptyTypeFrame, TypeFrameMeta, typeframe


class TestTypeFrame_Basic(unittest.TestCase):

    def test_emptytypeframe(self):
        # Cannot build a value:
        with self.assertRaises(RuntimeError):
            EmptyTypeFrame()

        # TODO :attempt to minimize the attack surface = minimize this !
        members = inspect.getmembers(EmptyTypeFrame)
        # compared to this
        ntmembers = inspect.getmembers(NamedTuple("EmptyNT", []))
        membdict = {n: v for n, v in members if (n, v) not in ntmembers}
        assert len(membdict) == 13  # TODO : refine test here...
        assert 'typeframe' in membdict

    @given(values = st.lists(st.integers(), max_size=5))
    def test_1field_typeframe_int(self, values: List[int]):
        # dynamic type declaration
        LoneValue = typeframe("LoneValue", columns=[("lonevalue", int)])

        with self.assertRaises(TypeError):
            LoneValue()
            # cannot be created without data...

        # build records
        lvl = [LoneValue(lonevalue=v) for v in values]

        for l in lvl:
            assert type(l) == type(lvl[0])  # consistency of types
            assert isinstance(type(l).lonevalue[l.lonevalue], sf.Frame)  # existence of property returning a dataframe
            assert len(type(l).lonevalue[l.lonevalue]) >= 1  # size if frame of self is one (or more)
            assert l in type(l)  # finding oneself ...
            assert type(l).typeframe is type(lvl[0]).typeframe  # unicity of the typeframe

        # slow but simple two by two equality check
        for la in lvl:
            assert hasattr(la, 'lonevalue')
            for lb in lvl:
                assert hasattr(lb, 'lonevalue')
                if la != lb:
                    assert (la == lb) == (la.lonevalue == lb.lonevalue)
                    # two type instances are same iff they have the same member value (usual tuple equality)

    @given(values = st.lists(st.tuples(st.integers(), st.text()), max_size=5))
    def test_2field_typeframe_int_str(self, values: List[Tuple[int, str]]):
        IntStrFrame = typeframe("IntStrFrame", columns=[("someint", int), ("somestr", str)])

        with self.assertRaises(TypeError):
            IntStrFrame()
            # cannot be created without data...

        # build records
        isfl = [IntStrFrame(someint=v[0], somestr=v[1]) for v in values]

        for isf in isfl:
            assert type(isf) == type(isfl[0])  # consistency of types
            assert isinstance(type(isf).someint[isf.someint], sf.Frame)  # existence of property returning a dataframe
            assert len(type(isf).someint[isf.someint]) >= 1  # size if frame of self is one (or more)
            assert isf in type(isf)  # finding oneself ...
            assert isinstance(type(isf).somestr[isf.somestr], sf.Frame)  # existence of property returning a dataframe
            assert len(type(isf).somestr[isf.somestr]) >= 1  # size if frame of self is one (or more)
            assert isf in type(isf)  # finding oneself ...
            assert type(isf).typeframe is type(isfl[0]).typeframe  # unicity of the typeframe

        # slow but simple two by two equality check
        for isfa in isfl:
            assert hasattr(isfa, 'someint')
            assert hasattr(isfa, 'somestr')
            for isfb in isfl:
                assert hasattr(isfb, 'someint')
                assert hasattr(isfb, 'somestr')
                if isfa != isfb:
                    assert (isfa == isfb) == ((isfa.someint == isfb.someint) and (isfa.somestr == isfb.somestr))
                    # two type instances are same iff they have the same member value (usual tuple equality)


# class TestTypeFrame_Properties(unittest.TestCase):
#
#     @given(tfa=st_TypeFrame(), tfb=st_TypeFrame())
#     def test_equality(self, tfa: Type[TypeFrame], tfb: Type[TypeFrame]):
#
#         eq = tfa == tfb
#         check = ((tfa().columns == tfb().columns) #TODO order should not matter here !
#                 and all(cta == ctb for cta, ctb in zip(tfa().column_types, tfb().column_types)))
#         assert check == eq
#
#     @given(nested=st_TypeFrame())
#     def test_implicit_join_dup(self, nested: TypeFrameBase):
#         IntStrNestedFrame = TypeFrame("TFTypeFrame", column_types=[
#             ("tf", nested),
#             ("highestlvl", int)])
#
#         FlattenFrame = TypeFrame("FlattenFrame", column_types=[
#             (f"tf.{f}", v) for f,v in nested.columns
#             ] + [
#             ("highestlvl", int)])
#
#         assert IntStrNestedFrame == FlattenFrame