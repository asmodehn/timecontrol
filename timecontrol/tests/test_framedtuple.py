import inspect
import unittest
from typing import List, Tuple, Type, NamedTuple

import static_frame as sf
import typing
from hypothesis import given, infer
import hypothesis.strategies as st

from timecontrol.tests.strats.st_framedtuple import st_FramedTuple, identifier_strategy, typehints_strategy
from timecontrol.framedtuple import FramedTupleMeta


class TestFramedTuple(unittest.TestCase):

    @given(ft=st_FramedTuple())
    def test_framedtuple(self,ft):
        raise NotImplementedError