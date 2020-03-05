import sys
import unittest

from timecontrol.eventcounter import EventCounter, Event, event


class TestEventCounter(unittest.TestCase):

    def test_counter(self):
        ec = EventCounter()

        e1 = event()
        assert isinstance(e1, Event)

        ec[e1] = 6

        assert ec[e1] == 6

    def test_sizeof(self):
        ec = EventCounter()

        e1 = event()
        assert isinstance(e1, Event)

        assert sys.getsizeof(ec) == 432, f"{sys.getsizeof(ec)} != "

        # adding a key increase the total size
        ec[e1] = 1
        assert sys.getsizeof(ec) == 524, f"{sys.getsizeof(ec)} != "

        # seems the count matters as well
        ec[e1] = sys.maxsize
        assert sys.getsizeof(ec) == 532, f"{sys.getsizeof(ec)} != "


if __name__ == '__main__':
    unittest.main()
