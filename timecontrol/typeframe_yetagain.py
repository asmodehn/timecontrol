from __future__ import annotations

from typing import NamedTupleMeta, NamedTuple
import static_frame as sf


class TypeFrameMeta(type):

    @classmethod
    def __prepare__(mcs, name, bases):

        # creating empty typeframe on the instance and adding it to the class (ie the type)
        # ns['typeframe'] = sf.Frame.from_records(records=[], columns=_ntbase._fields, dtypes=_ntbase._field_types)

        return {}

    def __new__(mcs, typename, bases, ns):

        # calling NamedTupleMeta to also process defaults values for this record type
        ntbase = NamedTupleMeta(typename=f"{typename}NamedTuple", bases=bases, ns=ns)

        # we create a typeframe from the ntbase structure
        ns['typeframe'] = sf.Frame.from_records(records=[], columns=ntbase._fields, dtypes=ntbase._field_types)

        # we create a class that inherits from namedtuple, but with our metaclass as a type.
        return super(TypeFrameMeta, mcs).__new__(mcs, f"{typename}", bases + (ntbase,), ns)

    def __init__(cls, typename, bases, ns):
        super(TypeFrameMeta, cls).__init__(typename, bases, ns)

    def __call__(cls, *args, **kwargs):
        # to wrap the behavior of the static __new__ in the class (and not the __new__ of the metaclass)
        inst = cls.__new__(cls, *args, **kwargs)

        # store into the frame
        records = [e for e in cls.typeframe.iter_tuple(1)]
        cls.typeframe = sf.Frame.from_records(records=records + [inst])

        return inst


if __name__ == '__main__':


    class MyType(metaclass=TypeFrameMeta):  # TODO : remove the metacalss here, no need to double up since we inherit from TYpeBase...
        # Note the cardinality is implicit here (could be added as parameter for TypeFrameMeta - making it value-dependent)
        col1: int
        col2: int

    class MyTypeBis(metaclass=TypeFrameMeta):
        mystrval: str


    print(MyType.typeframe)
    print(MyTypeBis.typeframe)

    mt = MyType(42, 56)
    assert mt.col1 == 42
    assert mt.col2 == 56

    mtb = MyTypeBis("bob")
    assert mtb.mystrval == "bob"

    print("\nTypeFrame MyType Records:")
    print([e for e in MyType])

    print("\nTypeFrame MyTypeBis Records:")
    print([e for e in MyTypeBis])