import aiounittest

from timecontrol.control import Control, ControlRunner


class TestControl(aiounittest.AsyncTestCase):
    def timer(self, incr=0):
        return self.clock

    def impl(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    async def impl_coro(self, *args):
        # args ignored
        self.command_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.slept = 0
        self.result = 42

        self.command_call = False

    async def test_control(self):
        # bound method or usual procedure usecase
        c = Control(timer=self.timer)(self.impl)
        assert self.command_call == False
        c_one = c(1, "2", "etc")
        assert isinstance(c_one, ControlRunner)

