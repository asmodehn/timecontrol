import unittest

from result import Err, Ok

from ..noexcept import noexcept


class TestNoexcept(unittest.TestCase):

    test_except = RuntimeError("desired exception for test")

    def noexcepted(self):
        self.noexcepted_call = True
        if self.wanted_except is not None:
            raise self.wanted_except
        return self.result

    def noexcepted_gen(self):
        self.noexcepted_call = True
        if self.wanted_except is not None:
            raise self.wanted_except
        yield self.result

    def setUp(self) -> None:
        self.wanted_except = None
        self.result = 42

        self.noexcepted_call = False

    def test_noexcept_function(self):

        bg_fun = noexcept(self.noexcepted)

        # after call we retrieve ok result
        assert bg_fun().is_ok()
        assert bg_fun().ok() == self.result

        self.wanted_except = self.test_except

        assert bg_fun().is_err()
        assert bg_fun().err() == self.test_except

    def test_noexcept_generator(self):

        bg_gen = noexcept(self.noexcepted_gen)

        # after call we retrieve ok result
        for yld in bg_gen():
            assert yld.is_ok()
            assert yld.ok() == self.result

        self.wanted_except = self.test_except

        for yld in bg_gen():
            assert yld.is_err()
            assert yld.err() == self.test_except


class TestNoexceptAsync(unittest.IsolatedAsyncioTestCase):

    test_except = RuntimeError("desired exception for test")

    async def async_noexcepted(self):
        self.noexcepted_call = True
        if self.wanted_except is not None:
            raise self.wanted_except
        return self.result

    async def async_noexcepted_gen(self):
        self.noexcepted_call = True
        if self.wanted_except is not None:
            raise self.wanted_except
        yield self.result

    def setUp(self) -> None:
        self.wanted_except = None
        self.result = 42

        self.noexcepted_call = False

    async def test_noexcept_async_function(self):

        bg_fun = noexcept(self.async_noexcepted)

        # after call we retrieve ok result
        assert (await bg_fun()).is_ok()
        assert (await bg_fun()).ok() == self.result

        self.wanted_except = self.test_except

        assert (await bg_fun()).is_err()
        assert (await bg_fun()).err() == self.test_except

    async def test_noexcept_async_generator(self):

        bg_gen = noexcept(self.async_noexcepted_gen)

        # after call we retrieve ok result
        async for yld in bg_gen():
            assert yld.is_ok()
            assert yld.ok() == self.result

        self.wanted_except = self.test_except

        async for yld in bg_gen():
            assert yld.is_err()
            assert yld.err() == self.test_except
