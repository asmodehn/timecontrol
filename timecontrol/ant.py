"""
Algebraic NamedTuple
"""
import types
from collections import OrderedDict
from typing import NamedTuple, Type

import typing

import wrapt
from _pytest.config import ExitCode
from hypothesis import given, infer
import hypothesis.strategies as st


def algebraic(pydef: typing.Union[NamedTuple, typing.Callable[..., NamedTuple]]):

    def product(self, other: typing.Union[NamedTuple, typing.Dict[str, Type], typing.Iterable[typing.Tuple[str, Type]]]):
        return NamedTuple(typename=f"{type(self).__name__}_x_{type(other).__name__}",
                            fields={**self.nt._field_types, **other._field_types})

    @wrapt.decorator
    def factory_decorator(wrapped, instance, args, kwargs):
        nt = wrapped(*args, **kwargs)
        nt.__mul__ = product  # adding a method to the class definition
        return nt

    @wrapt.decorator
    def type_decorator(wrapped, instance, args, kwargs):
        nt = wrapped(*args, **kwargs)
        nt.__mul__ = product
        return nt

    if isinstance(pydef, type):
        return type_decorator(pydef)
    else:
        return factory_decorator(pydef)


@algebraic
class Empty(NamedTuple):
    """
    The Initial Element of the PreOrder on number of fields.
    """
    pass


def test_record_empty():
    assert Empty._fields == ()
    assert Empty._field_types == OrderedDict()
    assert Empty._field_defaults == dict()


@given(field_types = st.dictionaries(keys=st.text(alphabet=st.characters(whitelist_categories=['Lu', 'Ll']), min_size=1, max_size=5),
                                     values=st.sampled_from(elements=[type(None), int, str])))
def test_record_create(field_types: typing.Dict[str, Type]):

    # dynamically build the record type
    MyRecord = algebraic(NamedTuple("MyRecord", fields=[ft for ft in field_types.items()]))

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
