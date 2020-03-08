from datetime import datetime

import hypothesis.strategies as st

from timecontrol.timeinterval import timeinterval


@st.composite
def st_timeinterval(draw, before: datetime =None, after:datetime=None):

    high = datetime.max
    low = datetime.min
    if before is not None:
        high = before
    if after is not None:
        low = after

    bl = draw(st.datetimes(min_value=low))
    bh = draw(st.datetimes(max_value=high))

    if bl > bh: # invert bounds if needed
        return timeinterval(start=bh, stop=bl)
    else:
        return timeinterval(start=bl, stop=bh)


if __name__ == '__main__':
    for n in range(1, 10):
        print(repr(st_timeinterval().example()))
