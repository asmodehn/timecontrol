
# Mixing call and result schedule.
# In hte same, but complementary way that we did for command log...
# TODO
import typing
from dataclasses import dataclass, field

from timecontrol.schedules.resultschedule import ResultSchedule


@dataclass(frozen=True)
class ControlExpect:

    # Note : Here the event semantic is the call : the important time is when call was started.
    result: typing.Optional[ResultSchedule] = field(default_factory=lambda: None)
