"""

Implementing an isomorphic repr (useful for our containers, especially dict/tree)

"""
from functools import singledispatch

import typing

from typeclasses import typeclass

T = typing.TypeVar('T')


@typeclass(T)
def isorepr(t: T):
    raise NotImplementedError


@isorepr.instance(str)
def _(t: str):
    return f"{t}: str"  # a string is its own representation


@isorepr.instance(int)
def _(i: int):
    return f"{i}: int"


# Other base types to allow some kind of structure :
#  {int} : sets  # no order - pointer and data are ints
#  [str] : list  # total order - pointer and data are str
#  <py> : tree  # partial order - pointer are py hashable and data are py data










def parserepr(r: str) -> typing.Any:
    """
    The parser inverse of the various repr.
    """

    # TODO : find a cleaner implementation...

    t = r[-3:]

    p = globals().get(t)
    if p is None:
        import builtins
        p = vars(builtins).get(t)
    return p(r[:-3-2])







if __name__ == '__main__':

    r34 = isorepr(34)
    pr34 = parserepr(r34)
    assert pr34 == 34, pr34

    r42 = isorepr('42')
    pr42 = parserepr(r42)
    assert pr42 == '42', pr42



