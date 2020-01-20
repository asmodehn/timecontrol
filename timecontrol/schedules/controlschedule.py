
# Mixing call and result schedule.
# In hte same, but complementary way that we did for command log...
# TODO
import typing
from dataclasses import dataclass, field

from timecontrol.schedules.callschedule import CallIntent
from timecontrol.schedules.resultschedule import ResultSchedule
from timecontrol.schedules.schedule import Schedule


@dataclass(frozen=True)
class ControlIntent(CallIntent):

    # Note : Here the event semantic is the call : the important time is when call was started.
    result: typing.Optional[ResultSchedule] = field(default_factory=lambda: None)


class ControlSchedule(Schedule):
    """
       """

    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self, *control_intents: ControlIntent):
        super(ControlSchedule, self).__init__(*control_intents)

    def __call__(
            self
    ):

        return super(ControlSchedule, self).__call__()
