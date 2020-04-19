from __future__ import annotations

from typing import NamedTupleMeta, NamedTuple
import static_frame as sf
import typing

import inspect

import hypothesis.strategies as st
import hypothesis.extra.numpy as npst


class EmptyFrameTupleMeta(type):
    """ Specific Empty (meta)type for FrameTuple, for code clarity.
    This is the Empty Type from ITT, but at the meta level.
    """

    def __new__(mcs, typename, bases, ns):
        return super(EmptyFrameTupleMeta, mcs).__new__(mcs, "EmptyFrameTuple", (), {})

    def __call__(cls, *args, **kwargs):
        raise RuntimeError("EmptyFrameTuple cannot be instantiated")

EmptyFrameTuple = EmptyFrameTupleMeta("EmptyFrameTuple", (), {})


class UnitFramedTupleMeta(type):
    """ Specific Unit (meta)type for FrameTuple, for code clarity.
    This is implemented as an empty tuple.
    There can potentially be multiple UnitTypes if the user make it so (via different typenames).
    There can be only one unit meta type however (keeping the ITT setup).
    """
    _unit: typing.ClassVar

    def __new__(mcs, typename, bases, ns):
        # if the same type already exist, return it !
        existing = UnitFrameTuples.get((typename,) + bases)
        if existing:
            return existing
        else:
            cls = super(UnitFramedTupleMeta, mcs).__new__(mcs, typename, bases, ns)
            cls._unit = cls()
            UnitFrameTuples[(typename,) + bases] = cls
            return cls

    def __init__(cls, typename, bases, ns):
        super(UnitFramedTupleMeta, cls).__init__(typename, bases, ns)

        cls._typename = typename

    def __call__(cls, *args, **kwargs):
        return cls._unit  # The only instance of the unit type

    def __repr__(cls):
        return f"<UnitFramedTuple <{cls._typename}> []>"

    def __eq__(cls, other: FramedTupleMeta):
        return (cls._typename == other._typename)

    # we need to keep the usual hash behavior, even if we redefine equality, to keep usual python tools behavior (debugger!)
    def __hash__(cls):  # TODO :  this need deep investigation...
        return type.__hash__(cls)

    def __iter__(cls):
        return cls._unit

    def __len__(cls):
        return 1


# TODO : avoid duplication, maybe there is already a location in the process global context ?
UnitFrameTuples = dict()


class EitherFrameTupleMeta(type):
    """ Specific Either (meta)type for FramedTuple, for code clarity."""

    _left: typing.ClassVar
    _right: typing.ClassVar

    def __new__(mcs, typename, bases, ns):
        cls = super(EitherFrameTupleMeta, mcs).__new__(mcs, typename, bases, ns)
        cls._unit = cls()

        return cls

    def __init__(cls, typename, bases, ns):
        super(FramedTupleMeta, cls).__init__(typename, bases, ns)

        # setting up typename
        cls._typename = typename

        # also setting up strategy
        cls._strategy = st.just(cls._unit)

    def __call__(cls, *args, **kwargs):
        raise NotImplementedError







class FramedTupleMeta(type):

    @classmethod
    def __prepare__(mcs, name, bases):

        # creating empty typeframe on the instance and adding it to the class (ie the type)
        # ns['typeframe'] = sf.Frame.from_records(records=[], columns=_ntbase._fields, dtypes=_ntbase._field_types)

        return {
            '_typemap': {  # a map to generate a python type...
                ''

            },
        }

    def __new__(mcs, typename, bases, ns):

        # dropping invalid annotations (None) to not have them created in the namedtuple and in the frame
        _nonefields = [a for a, t in ns.get("__annotations__", {}).items() if t is None or t is type(None)]

        if _nonefields:  # if at least one field is NoneType => we cannot create it => EmptyType
            return EmptyFrameTuple
            # This means we represent The EmptyType by NoneType
            # => a function returning None is a function that *never* returns

        # stripping NoneType fields for overall hygiene and sanity around here...
        ns['__annotations__'] = {a: t for a, t in ns.get("__annotations__", {}).items() if a not in _nonefields}

        # calling NamedTupleMeta to also process defaults values for this record type
        ntbase = NamedTupleMeta(typename=f"{typename}NamedTuple", bases=bases, ns={**ns, **{
            # redefining nametuple equality to be valid only inside a type
            '__eq__': lambda s, o: type(s) is type(o) and all(
                (type(getattr(s, f)), getattr(s, f)) == (type(getattr(s, f)), getattr(o, f)) for f in s._fields),
        }})

        if not ntbase._fields:  # No fields ! => Unit type => no elements => no Frame
            # we need to generate columns, types and strategies already while we have the tuple with proper python types
            ns['_columns'] = ()
            ns['_column_types'] = dict()
            ns['_column_strategies'] = []
            # TODO : defaults ?

            return UnitFramedTupleMeta(typename=typename, bases=bases + (ntbase,), ns=ns)

        else:
            # we need to generate columns, types and strategies already while we have the tuple with proper python types
            ns['_columns'] = ntbase._fields
            ns['_column_types'] = ntbase._field_types
            ns['_column_strategies'] = [(ft[0], st.from_type(ft[1])) for ft in ns['_column_types'].items()]
            # TODO : defaults ?

            # DO NOT TRUST dtypes here (empty frame doesnt record them)
            # we create a typeframe from the ntbase structure
            ns['frame'] = sf.Frame.from_records(records=[], columns=ntbase._fields)

            # we create a class that inherits from namedtuple, but with our metaclass as a type.
            return super(FramedTupleMeta, mcs).__new__(mcs, f"{typename}", bases + (ntbase,), ns)

    def __init__(cls, typename, bases, ns):
        super(FramedTupleMeta, cls).__init__(typename, bases, ns)

        # setting up typename
        cls._typename = typename

        # also setting up strategy
        cls._strategy = st.builds(cls, **{att: s for att, s in cls._column_strategies})

    def __call__(cls, *args, **kwargs):
        # to wrap the behavior of the static __new__ in the class (and not the __new__ of the metaclass)
        inst = cls.__new__(cls, *args, **kwargs)  # this will call namedtuple as usual since it is a baseclass

        # store into the frame
        records = [e for e in cls.frame.iter_tuple(1)]
        try:
            cls.frame = sf.Frame.from_records(records=records + [inst], columns=cls._columns, dtypes=cls._column_types)
        except ValueError as ve:
            print(f"ValueError : {inst} cannot be stored in the frame")
            raise ve
        except OverflowError as oe:
            print(f"OverflowError : {inst} cannot be strored in the frame")  # TODO :WORKINPROGRESS dependent typing for physical data bounds...
            raise oe
        return inst

    def __repr__(cls):
        # dtypes_dict = {k: v for k, v in self.frame.dtypes.items()}
        return f"<FramedTuple <{cls._typename}> {cls._column_types}>"

    def __eq__(cls, other: FramedTupleMeta):
        return other is not EmptyFrameTuple and (cls._typename == other._typename) and (cls._column_types == other._column_types)

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