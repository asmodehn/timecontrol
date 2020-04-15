"""
Algebraic NamedTuple
"""
import types
from collections import OrderedDict
from typing import NamedTuple, Type

import typing
from _pytest.config import ExitCode
from hypothesis import given, infer
import hypothesis.strategies as st


def algebraic(pydef):
    pass




# @algebraic
class Empty(NamedTuple):
    pass


def test_record_empty():
    assert Empty._fields == ()
    assert Empty._field_types == OrderedDict()
    assert Empty._field_defaults == dict()


@given(field_types = st.dictionaries(keys=st.text(alphabet=st.characters(whitelist_categories=['Lu', 'Ll']), min_size=1, max_size=5),
                                     values=st.sampled_from(elements=[type(None), int, str])))
def test_record_create(field_types: typing.Dict[str, Type]):

    # dynamically build the record type
    MyRecord = NamedTuple("MyRecord", fields=[ft for ft in field_types.items()])

    assert MyRecord._fields == tuple(k for k in field_types.keys())
    assert MyRecord._field_types == OrderedDict({f:t for f, t in field_types.items()})
    assert MyRecord._field_defaults == dict()  # skipping defaults for now





if __name__ == '__main__':
    import doctest
    # doctest for examples
    failed, attempted = doctest.testmod()

    import pytest
    # local typecheck
    # TODO tc = pytest.main(['-s', '--mypy', __file__])

    # full tests
    pt = pytest.main(['-s', '-v', __file__])

    # TODO : compute exit code...
    exit(failed * 100 + pt.value *10 ) #+ tc.value)
