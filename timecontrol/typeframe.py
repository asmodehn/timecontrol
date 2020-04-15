from __future__ import annotations
from typing import Iterable, Tuple, Any, NamedTuple, Optional, Type, ClassVar

import static_frame as sf


class TypeFrameBase:
    """
    Base class to represent a static frame as a bimonadic container representing a "Type" and its known elements
    """
    @staticmethod
    def Void():
        return TypeFrame("Void", column_types=[])

    frame: sf.FrameGO

    def __iter__(self):
        """ linear interface (towards the old)"""
        for e in reversed(self.frame):
            yield e

    def __len__(self):
        return len(self.frame)


def TypeFrame(typename: str, column_types: Iterable[Tuple[str, Any]]):


    struct = NamedTuple(typename=typename, fields=column_types)

    if not column_types:
        # Void usecase
        def frame_init(self):
            raise TypeError("No instance of this type can be constructed")

        return type(typename, (TypeFrameBase,), {"__init__": frame_init})

    def frame_init(self, *records: struct):
        if records:
            recs = [r for r in records if isinstance(r, struct)]  # type checking the record or dropping.
            # TODO : log/raise if something is dropped...
            self.frame = sf.FrameGO.from_records(records=recs)  # dtype supposedly guessed from records.
        else:
            self.frame = sf.FrameGO.from_records(records=[], columns=struct._fields, dtypes=struct._field_types)

    def frame_getitem(self, item: NamedTuple):
        return self.frame[item]

    def filter_factory(propname):
        def prop_filter(self):
            return {  #  a mapping to pick a value for this property as a filter
                v: frozenset(e for e in self.frame if getattr(e, propname) == v)
                for v in [getattr(e, propname) for e in self.frame]
            }

    attribs = {
        "Record": struct,
        "__init__": frame_init,
        "__getitem__": frame_getitem
    }

    # CAREFUL here : we need to have same behavioral interface as namedtuple...
    props = {f: property(filter_factory(f)) for f in struct._fields}

    frame = type(typename, (TypeFrameBase,), {**attribs, **props})

    return frame

# NoneTypeRecord = NamedTuple("NoneType",)
# NoneInstance = NoneTypeRecord()
# NoneTypeFrame = TypeFrame(records=[NoneInstance], record_type=NoneTypeRecord)


# def typeframe(name: str, *, records: Optional[Iterable[Any]], record_type: Optional[NamedTuple] = None):
#
#     if not records:  # no records
#         if record_type is None:
#             return TypeFrame.Void()
#         else:
#             # although empty, we have some shape already
#             tf = TypeFrame(record_type=record_type)
#     else:
#         tf = TypeFrame(records=records)
#     return tf








if __name__ == '__main__':

    TypeFrame("MyType", fields=[("nickname", str)])