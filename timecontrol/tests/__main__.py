import unittest

"""
Embedded tests, to validate on user installation.
uses integrated python tools only.
"""


# import your test modules
if __package__ is not None:
    from . import test_underlimiter, test_overlimiter
else:
    import test_underlimiter, test_overlimiter

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(test_underlimiter))
suite.addTests(loader.loadTestsFromModule(test_overlimiter))

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)

if result.wasSuccessful():
    exit(0)
else:
    exit(1)
