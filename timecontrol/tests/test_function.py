import unittest

from ..function import Function


class TestFunction(unittest.TestCase):

    def timer(self, incr=0):
        return self.clock

    def funimpl(self, input):
        # ignoring input : constant function
        self.functional_call = True
        return self.result

    def setUp(self) -> None:
        self.clock = 0
        self.result = 42

        self.functional_call = False

    def test_functionality(self):
        f = Function(self.funimpl)
        assert self.functional_call == False
        assert f[1] == 42
        assert self.functional_call == True
        self.functional_call = False
        assert f[1] == 42
        assert self.functional_call == False
        assert f[51] == 42
        assert self.functional_call == True
