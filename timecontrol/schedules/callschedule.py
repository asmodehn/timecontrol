import random
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections.abc import MutableMapping

import typing

import dpcontracts
import asyncio

from timecontrol.schedules.schedule import Schedule, Intent

"""
A Schedule of intents
intents have a targetdate to start getting into effect

"""


@dataclass(frozen=True)
class CallIntent(Intent):

    args_strat = ()  # TODO : generator / strategy
    kwargs_strat = {}  # TODO : generator / strategy

    def __init__(self, args_strat: typing.Iterable =None, kwargs_strat: typing.Iterable =None):  # TODO match arguments from callable / hypothesis-like
        object.__setattr__(self, 'args_strat', args_strat if args_strat is not None else random.random(0, 1))
        object.__setattr__(self, 'kwargs_strat', kwargs_strat if kwargs_strat is not None else random.random(0, 1))

        super(CallIntent, self).__init__()

    def __hash__(self):  # make sure the event is hashable (storable in a set)
        return hash(self.targetdate)

    def __call__(self):  # Note: This is a simulation algorithm !
        #print(f"target: {self.targetdate} clock: {datetime.now(tz=timezone.utc)}")

        # TODO : proper generator
        args = random.sample(self.args_strat, 1)[0]
        kwargs = random.sample(self.kwargs_strat.items(), 1)[0]
        return (args, kwargs)


class CallSchedule(Schedule):
    """
       """

    # NOTE:DO NOT combine with the log, semantic is quite different
    # => how about events that were not intended and intents that didn't happen ??
    def __init__(self, *call_intents: CallIntent):
        super(CallSchedule, self).__init__(*call_intents)

    def __call__(
            self
    ):

        return super(CallSchedule, self).__call__()


# def scheduled(schedule: Schedule):
#     def decorator(cmd):
#         # TODO : nice and clean wrapper
#         def wrapper(*args, **kwargs):
#             scheduled[datetime.now()] = Intent(cmd, args, kwargs)
#         return wrapper
#     return decorator


if __name__ == "__main__":

    args_gen = [ 1,2,3,4,5,6, ]
    kwargs_gen = {'a':1, 'b': 2}

    i1 = CallIntent(args_strat= args_gen, kwargs_strat=kwargs_gen)

    i2 = CallIntent(args_strat= args_gen, kwargs_strat=kwargs_gen)

    s = CallSchedule(i1, i2)

    assert s() == i1

    args, kwargs = i1()

    assert args in args_gen
    assert kwargs[0] in kwargs_gen and kwargs[1] == kwargs_gen[kwargs[0]]

    assert s() == i2


