import unittest

from timecontrol.utils.reactor import reactor


class TestReactorCallable(unittest.TestCase):

    def effector(self, arg):
        self.effected = arg
        return 51  # return should be ignored !

    def reactored(self, **kwargs):
        self.reactored_call = True
        return self.result, kwargs

    def reactored_gen(self, **kwargs):
        self.reactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.effected = None
        self.effecting_reactor = reactor(effector=self.effector)  # Note we don't need anything to initialize effector

        self.reactored_call = False

    def test_reactor_function(self):

        reacting = self.effecting_reactor(self.reactored)

        reacting(answer=42)
        assert self.effected == (42, {'answer': 42})

    def test_reactor_generator(self):

        reacting = self.effecting_reactor(self.reactored_gen)

        for yld in reacting(answer=42):  # decorated method remains a generator
            assert yld == (42, {'answer': 42})
            assert self.effected == (42, {'answer': 42})

        assert self.effected == (42, {'answer': 42})


class TestAsyncReactorCallable(unittest.IsolatedAsyncioTestCase):

    def effector(self, arg):
        self.effected = arg
        return 51  # return should be ignored !

    def reactored(self, **kwargs):
        self.reactored_call = True
        return self.result, kwargs

    def reactored_gen(self, **kwargs):
        self.reactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.effected = None
        self.effecting_reactor = reactor(effector=self.effector)  # Note we don't need anything to initialize effector

        self.reactored_call = False

    def test_reactor_function(self):

        reacting = self.effecting_reactor(self.reactored)

        reacting(answer=42)
        assert self.effected == (42, {'answer': 42})

    def test_reactor_generator(self):

        reacting = self.effecting_reactor(self.reactored_gen)

        for yld in reacting(answer=42):  # decorated method remains a generator
            assert yld == (42, {'answer': 42})
            assert self.effected == (42, {'answer': 42})

        assert self.effected == (42, {'answer': 42})


class TestReactorGenerator(unittest.TestCase):

    def effector(self):
        sent = None  # startup
        while True:
            sent = yield sent  # storing in sent to have something to yield for next loop iteration...
            self.effected.append(sent)

    async def reactored(self, **kwargs):
        self.reactored_call = True
        return self.result, kwargs

    async def reactored_gen(self, **kwargs):
        self.reactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.effected = []
        self.effecting_reactor = reactor(effector=self.effector())

        self.reactored_call = False

    async def test_reactor_function(self):

        reacting = self.effecting_reactor(self.reactored)

        await reacting(answer=42)
        assert self.effected == [(42, {'answer': 42})]

    async def test_reactor_generator(self):

        reacting = self.effecting_reactor(self.reactored_gen)

        async for yld in reacting(answer=42):  # decorated method remains a generator
            assert yld == (42, {'answer': 42})  # sent args passed as is to the generator...
            assert self.effected == [(42, {'answer': 42})]  # already sent to effector as it is a generator

        assert self.effected == [(42, {'answer': 42})]


class TestAsyncReactorGenerator(unittest.IsolatedAsyncioTestCase):

    def effector(self):
        while True:
            sent = yield
            self.effected.append(sent)

    async def reactored(self, **kwargs):
        self.reactored_call = True
        return self.result, kwargs

    async def reactored_gen(self, **kwargs):
        self.reactored_call = True
        yield self.result, kwargs

    def setUp(self) -> None:
        self.result = 42

        self.effected = []
        self.effecting_reactor = reactor(effector=self.effector())

        self.reactored_call = False

    async def test_reactor_function(self):

        reacting = self.effecting_reactor(self.reactored)

        await reacting(answer=42)
        assert self.effected == [(42, {'answer': 42})]

    async def test_reactor_generator(self):

        reacting = self.effecting_reactor(self.reactored_gen)

        async for yld in reacting(answer=42):  # decorated method remains a generator
            assert yld == (42, {'answer': 42})  # sent args passed as is to the generator...
            assert self.effected == [(42, {'answer': 42})]  # already sent to effector as it is a generator

        assert self.effected == [(42, {'answer': 42})]


if __name__ == '__main__':
    unittest.main()
