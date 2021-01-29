from __future__ import annotations

import time
from abc import abstractmethod
from collections.abc import Iterator
from typing import (
    Any, AsyncGenerator, Callable, Generator, List, MutableMapping, Optional, Protocol, Sequence, MutableSequence,
    TypeVar, Union,
)

# Dual of an iterable

T = TypeVar('T', contravariant=True)
class Aggregatable(Protocol[T]):

    @abstractmethod
    def _aggr_(self) -> Aggregator[T]:
        "dual to __iter__()"
        raise NotImplementedError

# Dual of an iterator
class Aggregator(Aggregatable[T]):

    @abstractmethod
    def _drop_(self, value: T) -> None:
        "dual to __next__()"
        raise NotImplementedError



# dual to next(), calling instance method...
# TODO : single dispatch ???
def drop(object: Union[Aggregator], value: T) -> None:
    object._drop_(value)


# Ref : https://docs.python.org/3/library/collections.abc.html


# We need custom classes to implement this protocol...
class list_aggregator(list, Aggregator[T]):

    def __init__(self, *args, **kwargs):
        super(list_aggregator, self).__init__(*args, **kwargs)

    def _aggr_(self) -> Aggregator[T]:
        return self

    def _drop_(self, value: T) -> None:
        self.append(value)


# We need custom classes to implement this protocol...
class dict_aggregator(dict, Aggregator[T]):

    def __init__(self, *args, **kwargs):
        self._cur = time.time()  # initialize timer... TODO : coulc also be from sentinel?
        super(dict_aggregator, self).__init__(*args, **kwargs)

    def _aggr_(self) -> Aggregator[T]:
        return self

    def _drop_(self, value: T) -> None:
        self._cur = time.time()  # using local time as the key...
        self.__setitem__(self._cur, value)


# This works with normal python types, but will add a layer of custom classes to use the aggregator protocol...
# TODO : single dispatch ?
def aggr(object: Union[MutableSequence, MutableMapping, Generator[...], AsyncGenerator[...]], sentinel: Optional[Any] = None):
    """
    We are here attempting to be dual to iter():

        Return an aggregator object. The first argument is interpreted very differently depending on the presence of the second argument.
        Without a second argument, object must be a collection object which supports aggregating elements  (like list.append()),
         or it must support the mutable sequence protocol (the __setitem__() method with integer arguments starting at 0).
         If it does not support either of those protocols, TypeError is raised.

         If the second argument, sentinel, is given, then object must be a callable object.
         The iterator created in this case will call object with no arguments for each call to its __next__() method;
         if the value returned is equal to sentinel, StopIteration will be raised, otherwise the value will be returned.

    One useful application of the second form of aggr() is to build a block-writer.
    For example, reading fixed-width blocks from a binary database file until the end of file is reached:

    from functools import partial
    with open('mydata.db', 'rb') as f:
        for block in iter(partial(f.read, 64), b''):
            process_block(block)


    :param aggregable:
    :return:
    """

    if sentinel is not None:
        raise NotImplementedError
    else:
        if isinstance(object, list):
            return list_aggregator(object)
        elif isinstance(object, MutableMapping):
            return dict_aggregator(object)
        else:
            raise NotImplementedError
