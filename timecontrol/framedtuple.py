from __future__ import annotations

from typing import NamedTupleMeta, NamedTuple
import static_frame as sf
import typing

import inspect

import hypothesis.strategies as st

class FramedTupleMeta(type):

    @classmethod
    def __prepare__(mcs, name, bases):

        # creating empty typeframe on the instance and adding it to the class (ie the type)
        # ns['typeframe'] = sf.Frame.from_records(records=[], columns=_ntbase._fields, dtypes=_ntbase._field_types)

        # return {
        #     '_stratmap': {  # a map to pick strategy based on a type, and draw when generating
        #         None: st.none(),
        #         int: st.integers(),
        #         str: st.text(max_size=8),
        #     },
        #     '_typemap': {  # a map to convert a numpy dtype into a python type...
        #
        #     },
        # }
        return {}

    def __new__(mcs, typename, bases, ns):

        # calling NamedTupleMeta to also process defaults values for this record type
        ntbase = NamedTupleMeta(typename=f"{typename}NamedTuple", bases=bases, ns=ns)

        # we create a typeframe from the ntbase structure
        ns['frame'] = sf.Frame.from_records(records=[], columns=ntbase._fields, dtypes=ntbase._field_types)

        # we create a class that inherits from namedtuple, but with our metaclass as a type.
        return super(FramedTupleMeta, mcs).__new__(mcs, f"{typename}", bases + (ntbase,), ns)

    def __init__(cls, typename, bases, ns):
        super(FramedTupleMeta, cls).__init__(typename, bases, ns)

        cls._typename = typename

    def __call__(cls, *args, **kwargs):
        # to wrap the behavior of the static __new__ in the class (and not the __new__ of the metaclass)
        inst = cls.__new__(cls, *args, **kwargs)  # this will call namedtuple as usual since it is a baseclass

        # store into the frame
        records = [e for e in cls.frame.iter_tuple(1)]
        cls.frame = sf.Frame.from_records(records=records + [inst])

        return inst

    @property
    def _columns(cls):  # this is the structure of the type, but can also be dynamic !
        return list(cls.frame.columns)

    @property
    def _column_types(cls):  # this is the structure of the type, but can also be dynamic !
        return [dt for dt in cls.frame.dtypes.items()]

    def __repr__(cls):
        # dtypes_dict = {k: v for k, v in self.frame.dtypes.items()}
        return f"<FramedTuple <{cls._typename}> {cls._column_types}>"

    def __eq__(cls, other: FramedTupleMeta):
        return (cls._columns == other._columns) and (cls._column_types == other._column_types)

    # we need to keep the usual hash behavior, even if we redefine equality, to keep usual python tools behavior (debugger!)
    def __hash__(cls):  # TODO :  this need deep investigation...
        return type.__hash__(cls)

    def __iter__(cls):
        for e in cls.frame.iter_tuple(1):
            # recreating the record instance on the fly, (without registering in frame again)
            yield cls.__new__(cls, **e._asdict())

    def __len__(cls):
        return len(cls.frame)


def FramedTuple(typename, columns: typing.Iterable[typing.Tuple[str, typing.Type]]):

    # dynamically building a frametuple
    return FramedTupleMeta(typename=typename, bases=(), ns={
        '__annotations__': {
            c: th for c, th in columns
        }
    })
    #  TODO : keep as close as possible to NamedTuple interface (but maybe not the code design ?)
    # => default values are not supported in this way

    # TODO : maybe a way to have inheritance of FramedTuple have the NamedTuple behavior ??? OR NOT ???


if __name__ == '__main__':

    class MyType(metaclass=FramedTupleMeta):  # TODO : remove the metacalss here, no need to double up since we inherit from TYpeBase...
        # Note the cardinality is implicit here (could be added as parameter for TypeFrameMeta - making it value-dependent)
        col1: int
        col2: int

    MyTypeBis = FramedTuple(typename='MyTypeBis', columns=[('mystrval', str)])


    print(MyType.frame)
    print(MyTypeBis.frame)

    print(MyType._columns)
    print(MyType._column_types)

    mt = MyType(42, 56)
    repr(mt)
    assert mt.col1 == 42
    assert mt.col2 == 56

    assert MyType == MyType
    assert MyType != MyTypeBis

    mtb = MyTypeBis("bob")
    assert mtb.mystrval == "bob"

    assert len(MyType) == 1
    print("\nTypeFrame MyType Records:")
    print([e for e in MyType])

    assert len(MyTypeBis) == 1
    print("\nTypeFrame MyTypeBis Records:")
    print([e for e in MyTypeBis])