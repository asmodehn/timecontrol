import inspect
from collections import OrderedDict, namedtuple
from collections.abc import Mapping
from datetime import datetime

from timecontrol.logs.calllog import CommandCalled, CallLog
from timecontrol.logs.resultlog import CommandReturned, ResultLog

CmdSyncLogData = namedtuple("CmdSyncLog", ["call", "result"])


class CmdSyncLog(Mapping):
    """
       This is a synchronous command log, as a wallclock-indexed event datastore (immutable observed event can be almost anything).
       It is callable, to store a value with the current (wall)clock.
       """

    def __init__(self, timer=datetime.now):
        self.timer = timer
        self.sigmap = OrderedDict()  # Needed ?? stored in closure, but not really explicit...
        self.calllogs = OrderedDict()
        self.resultlogs = OrderedDict()
        self.flow = OrderedDict()  # a special case of ASync

    def __call__(self, cmd):  # decorator
        sig = inspect.Signature.from_callable(cmd)
        if sig not in self.sigmap:
            self.sigmap[cmd.__name__] = sig
            self.calllogs[cmd.__name__] = CallLog()
            self.resultlogs[cmd.__name__] = ResultLog()

        # TODO : nice wrapper (wrapt or other)
        # Note : sig is stored in the closure here...
        def wrapper(*args, **kwargs):
            # storing the call
            call_evt = self.calllogs[cmd.__name__](CommandCalled(args=args, kwargs=kwargs))
            # binding args and kwargs
            ba = sig.bind(*args, **kwargs)
            # doing the call
            res = cmd(*ba.args, **ba.kwargs)
            # storing the return
            result_evt = self.resultlogs[cmd.__name__](CommandReturned(res))
            # storing the flow (reminder : world time is part of the call event)
            self.flow[call_evt] = result_evt
            return res  # return it

        return wrapper

    def __getitem__(self, cmd):
        """
        Return a list of related calls and results
        :param cmd:
        :return:
        """
        cmdsynclog = OrderedDict()
        if cmd in self.calllogs:
            for call, evt in self.calllogs[cmd].items():
                cmdsynclog[call] = (evt, {self.flow.get(e) for e in evt}) # TODO : some trick to pick one elem from the set...
            return cmdsynclog
        else:
            return KeyError(f"Command {cmd} was never called")

    def __iter__(self):
        return iter(self.calllogs)

    def __len__(self):
        return len(self.calllogs)


if __name__ == '__main__':

    import random

    log = CmdSyncLog()

    @log
    def rand(p):
        return random.randint(0, p)

    r42 = rand(42)
    r53 = rand(53)

    for c, r in log['rand'].items():
        print(f" - {c} => {r}")
