import unittest

"""
Embedded tests, to validate on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import (
        test_calllimiter,
        test_callscheduler
    )
else:
    import test_calllimiter, test_callscheduler

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_calllimiter))
suite.addTests(loader.loadTestsFromModule(test_callscheduler))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
