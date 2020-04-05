import hypothesis.strategies as st
import typing

from hypothesis.strategies import SearchStrategy

from timecontrol.agentschedule import schedule

@st.composite
def st_timepoint(draw):
    tp = draw(st.datetimes())
    return tp.timestamp()

@st.composite
def st_awaitable(draw, like=lambda: None, returns=st.integers()):  # return integers to allow impurity on run
    f = draw(st.functions(like=like, returns=returns))

    # building an awaitable from a coro.
    async def coro(*args, **kwargs):
        return f(*args, **kwargs)

    # CAREFUL : coro run are considered indeterministic: two runs with same params are differents
    return coro
# TODO : maybe should be in hypothesis itself ?


@st.composite
def st_agentschedule(draw, awaitable_strat: SearchStrategy = st_awaitable()):

    sched = draw(st.dictionaries(keys=st_timepoint(), values=awaitable_strat, max_size=5))
    return schedule(sched)


if __name__ == '__main__':
    for n in range(1, 10):
        print(repr(st_agentschedule().example()))
