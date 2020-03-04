import hypothesis.strategies as st

from timecontrol.timeslice import timeslice


@st.composite
def st_timeslice(draw):

    return timeslice(
        start=draw(st.datetimes()),
        stop=draw(st.datetimes()),
        step=draw(st.timedeltas()),
    )


if __name__ == '__main__':
    for n in range(1, 10):
        print(repr(st_timeslice().example()))
