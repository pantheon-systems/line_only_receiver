import random
import time

from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet import task

from tx_tcp_line_client import retry

class TestError(Exception): pass

MAX_RETRIES = 7

class RetryTestCase(unittest.TestCase):
    def setUp(self):
        self.counter = 0
        def test_function(succeed_after=None):
            if self.counter >= succeed_after:
                return defer.succeed('I PASSED')
            self.counter +=1
            return defer.fail(TestError())
        self.decorator = retry.Retry(MAX_RETRIES, (TestError,))
        self.decorator.clock = task.Clock()
        self.decorated_func = self.decorator(test_function)
        self.undecorated_func = test_function

    def tearDown(self):
        self.assertFalse(
            self.decorator.clock.calls,
            "The reactor was unclean. {}".format(self.decorator.clock.calls)
        )

def _succeed_after_test_case_factory(succeed_after):
    def test_success_case(self):
        d = self.decorated_func(succeed_after)
        for i in xrange(succeed_after):
            self.decorator.clock.advance(3600)
        d.addCallback(self.assertEqual, 'I PASSED')
    return test_success_case

for succeed_after in xrange(MAX_RETRIES+1):
    setattr(
        RetryTestCase,
        'test_retry_succeed_on_attempt_{}'.format(succeed_after),
        _succeed_after_test_case_factory(succeed_after)
    )
