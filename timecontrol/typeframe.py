from typing import NamedTupleMeta
import static_frame as sf


class TypeFrameMeta(type):

    def __new__(cls, typename, bases, ns):
        if ns.get('_rootframe', False):
            # The Special case of TypeFrame base class (also used as Empty type)

            # calling NamedTupleMeta to also process defaults values for this record type
            ns['Record'] = NamedTupleMeta(typename=f"{typename}Record", bases=bases, ns={})

            # creating empty typeframe and adding it to the type
            ns['typeframe'] = sf.Frame.from_records(records=[], columns=[])
            return super().__new__(cls, typename, bases, ns)

        # calling NamedTupleMeta to also process defaults values for this record type
        ns['Record'] = NamedTupleMeta(typename=f"{typename}Record", bases=bases, ns=ns)

        # creating empty typeframe and adding it to the type
        ns['typeframe'] = sf.Frame.from_records(records=[], columns=ns['Record']._fields, dtypes=ns['Record']._field_types)

        def property_reindex(propname):
            def reindexer(self):
                return {k: sf.Frame.from_records(records=[r for r in self.typeframe.iter_tuple(1) if getattr(r, propname) == k])
                        for k in set(getattr(e, propname) for e in self.typeframe.iter_tuple(1))}  # TODO : find a faster way...
            return reindexer

        for p in ns['typeframe'].columns:
            # property of a class needs to be defined on the metaclass!
            setattr(cls, p, property(property_reindex(propname=p)))

        return super().__new__(cls, typename, bases, ns)

    def __len__(self):
        return len(self.typeframe)


class TypeFrame(metaclass=TypeFrameMeta):
    """

    """
    _rootframe = True

    def __new__(cls, *args, **kwargs):
        # calling the record type and returning it after storage
        inst = cls.Record(*args, **kwargs)
        records = [e for e in cls.typeframe.iter_tuple(1)]
        cls.typeframe = sf.Frame.from_records(records=records + [inst])
        return inst


class MyType(TypeFrame, metaclass=TypeFrameMeta):
    _rootframe = False
    # Note the cardinality is implicit here (could be added as parameter for TypeFrameMeta)
    col1: int
    col2: int


if __name__ == '__main__':

    print(MyType.Record)
    print(MyType.typeframe)

    mt = MyType(42, 56)
    print([e for e in MyType.typeframe.iter_tuple(1)])
    print(MyType.col1[42])
    try:
        print(MyType.col1[53])
    except KeyError as ke:
        print(f"KeyError: {ke}")
    print(len(MyType))




