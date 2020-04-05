import time
import unittest

from hypothesis import given
import hypothesis.strategies as st

from timecontrol.agentschedule import schedule, AgentSchedule
from timecontrol.tests.strats.st_agentschedule import st_agentschedule, st_awaitable, st_timepoint


class TestAgentSchedule(unittest.TestCase):

    # Test inspired from D. Ahman (containers as bimonads)
    @given(sched = st_agentschedule())
    def test_implicit_join_dup(self, sched):

        s = schedule(sched)
        assert isinstance(s, AgentSchedule)

        s1 = schedule(schedule(sched))
        assert isinstance(s1, AgentSchedule)

        assert s1 == s, f" ERROR: monadic join not respected on init: {s1} != {s}"
        assert s == s1, f" ERROR: comonadic dup not respected init: {s} != {s1}"

    @given(sched=st_agentschedule(), t=st_timepoint(), coro=st_awaitable())
    def test_return_extract_coro(self, sched, t, coro):
        coro_inst = coro()
        local_sched = schedule({t: coro_inst})

        assert local_sched[t] == coro_inst

        # mutable
        coro_inst = coro()
        sched[t] = coro_inst

        # extract
        assert sched[t] == coro_inst

    @given(sched1=st_agentschedule(), sched2=st_agentschedule())
    def test_merge_schedule(self, sched1, sched2):

        # immutability
        old_sched1 = sched1.copy()
        old_sched2 = sched2.copy()

        merged = sched1 * sched2

        assert sched1 == old_sched1
        assert sched2 == old_sched2

        assert len(merged) == len(sched1) + len(sched2)

        # time might be slightly different, but we need to make sure all actions are there
        # TODO : think about a way to collapse time without loosing actions...
        for a in sched1.values():
            assert a in merged.values()

        for a in sched2.values():
            assert a in merged.values()

    # TODO : maybe test for a full Huet Zipper ??
