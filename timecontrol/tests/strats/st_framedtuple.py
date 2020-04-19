import unittest
from datetime import datetime
import static_frame as sf

import hypothesis.strategies as st
from hypothesis import given
from hypothesis.strategies import SearchStrategy

from timecontrol.framedtuple import FramedTuple, FramedTupleMeta
from timecontrol.typeframe import TypeFrameMeta, typeframe

identifier_strategy = st.text(alphabet=st.characters(whitelist_categories=['Lu', 'Ll'], max_codepoint=127),  min_size=1, max_size=5)
typehints_strategy = st.sampled_from(elements=[type(None), int, str])  # TODO : extend the list of possible core types


@st.composite
def st_FramedTuple(draw, typehints: SearchStrategy=typehints_strategy):

    # TODO : more possible content, potentially data structures...
    typename = draw(identifier_strategy)
    fields = draw(st.dictionaries(keys=identifier_strategy, values=typehints_strategy, min_size=1, max_size=5)).items()
    return FramedTuple(typename=typename, columns=fields)


class TestStrategy(unittest.TestCase):

    @given(typename=identifier_strategy, columns=st.dictionaries(keys=identifier_strategy, values=typehints_strategy, min_size=1, max_size=5))
    def test_class_declaration(self, typename, columns):
        ft = FramedTupleMeta(typename, bases=(), ns={
            '__annotations__': columns,
        })  # TODO : find a better way to simulate class delcaration...

        assert hasattr(ft, 'frame') and type(ft.frame) == sf.Frame
        assert hasattr(ft, '_columns') and hasattr(ft, '_column_types')

        # generate a value


    @given(typename=identifier_strategy, columns=st.dictionaries(keys=identifier_strategy, values=typehints_strategy, min_size=1, max_size=5))
    def test_dynamic_declaration(self, typename, columns):
        ft = FramedTuple(typename=typename, columns=[c for c in columns.items()])

        assert hasattr(ft, 'frame') and type(ft.frame) == sf.Frame
        assert hasattr(ft, '_columns') and hasattr(ft, '_column_types')

        # generate a value
        # t = ft()


if __name__ == '__main__':
    for n in range(1, 10):
        ft = st_FramedTuple().example()
        # TODO : a way to sample elements ( default values ? strategy ? )
        print(f"{repr(ft)}")

    unittest.main()
