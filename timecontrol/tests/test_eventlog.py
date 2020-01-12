import unittest

from ..eventlog import EventLog


class TestFunction(unittest.TestCase):
    def timer(self):
        return self.clock

    def command(self):
        self.logged_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.result = 42

        self.logged_call = False

    def test_logger_mapping(self):
        f = EventLog(timer=self.timer)

        assert f(42) == 42  # pure side effect

        assert f[0] == {42}

        assert f(51) == 51

        assert f[0] == {42, 51}

        self.clock += 1

        assert f[1] == set()

        assert f(32) == 32

        assert f[1] == {32}

    def test_logger_last(self):
        f = EventLog(timer=self.timer)

        assert f(42) == 42  # pure side effect

        assert f[0] == {42}

        assert f(51) == 51

        assert f[0] == {42, 51}

        assert f.last in [51, 42]  # expected indeterminism

        self.clock += 1

        assert f[1] == set()

        assert f(32) == 32

        assert f[1] == {32}

        assert f.last == 32

    def test_logger_elems(self):
        f = EventLog(timer=self.timer)

        assert f(42) == 42

        assert f[0] == {42}

        assert f(42) == 42

        assert f[0] == {42}

        assert f(51) == 51

        assert f[0] == {42, 51}
