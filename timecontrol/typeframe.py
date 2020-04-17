from typing import NamedTupleMeta, Any, Tuple, Iterable
import static_frame as sf


class TypeFrameMeta(type):

    def __new__(mcls, typename, bases, ns):

        # calling NamedTupleMeta to also process defaults values for this record type
        ntbase = NamedTupleMeta(typename=f"{typename}NamedTuple", bases=bases, ns=ns)
        # This will be used as a base class, and we will override some of its functionalities for the frame usecase

        # creating empty typeframe and adding it to the type
        ns['typeframe'] = sf.Frame.from_records(records=[], columns=ntbase._fields, dtypes=ntbase._field_types)

        ### modifying the metaclass (to modify the behavior of the type itself)
        def property_reindex(propname):
            def reindexer(self):
                return {k: sf.Frame.from_records(records=[r for r in self.typeframe.iter_tuple(1) if getattr(r, propname) == k])
                        for k in set(getattr(e, propname) for e in self.typeframe.iter_tuple(1))}  # TODO : find a faster way...
            return reindexer

        for p in ns['typeframe'].columns:
            # property of a class needs to be defined on the metaclass!
            setattr(mcls, p, property(property_reindex(propname=p)))

        def cls_iter(cls):
            for e in cls.typeframe.iter_tuple(1):
                # recreating the record type instance (without registering in frame again)
                yield ntbase.__new__(cls, **e._asdict())

        mcls.__iter__ = cls_iter


        ### modifying the class (to modify the behavior of instance)
        def cls_new(cls, *args, **kwargs):
            # special case for EmptyTypeFrame
            if not cls._fields:
                raise RuntimeError("Empty Type cannot be instantiated")

            # calling the record type and returning it after storage
            inst = ntbase.__new__(cls, *args, **kwargs)  # delegating to namedtuple constructor
            records = [e for e in cls.typeframe.iter_tuple(1)]
            cls.typeframe = sf.Frame.from_records(records=records + [inst])
            return inst

        ns['__new__'] = cls_new

        return super().__new__(mcls, typename, bases + ( ntbase, ), ns)

    def __len__(self):
        return len(self.typeframe)


def typeframe(typename: str, columns: Iterable[Tuple[str, Any]]):
    """
    Dynamic creation of a typeframe
    :param typename:
    :param fields:
    :return:
    """

    ns = {
        '__module__': __name__,
        '__qualname__': typename,
        '__annotations__': {k: v for k, v in columns} }

    return TypeFrameMeta.__new__(TypeFrameMeta, typename=typename, bases=(), ns=ns)


# Empty Type exist but an instance cannot be created.
class EmptyTypeFrame(metaclass=TypeFrameMeta):
    pass


class MyType(metaclass=TypeFrameMeta):  # TODO : remove the metacalss here, no need to double up since we inherit from TYpeBase...
    # Note the cardinality is implicit here (could be added as parameter for TypeFrameMeta - making it value-dependent)
    col1: int
    col2: int


if __name__ == '__main__':

    print(MyType.typeframe)

    mt = MyType(42, 56)
    assert mt.col1 == 42

    print([e for e in MyType.typeframe.iter_tuple(1)])

    # equality of frame based on content
    assert MyType.col1[42] == sf.Frame.from_records(records=[mt])

    try:
        print(MyType.col1[53])
    except KeyError as ke:
        print(f"KeyError: {ke}")

    mtbis = MyType(51, 63)
    print(mtbis)

    print(len(MyType))




