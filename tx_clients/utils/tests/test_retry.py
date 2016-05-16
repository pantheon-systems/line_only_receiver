import random
import time

from twisted.trial import unittest
from twisted.internet import defer
from twisted.internet import task

from tx_clients.utils import retry
from tx_clients.exceptions import TimeoutError

MAX_RETRIES = 7

class RetryTestCase(unittest.TestCase):
    def setUp(self):
        self.counter = 0
        def test_function(succeed_after=None):
            if self.counter >= succeed_after:
                return defer.succeed('I PASSED')
            self.counter +=1
            return defer.fail(TimeoutError())
        self.decorator = retry.Retry(MAX_RETRIES, (TimeoutError,))
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

def _fail_after_test_case_factory(succeed_after):
    def test_fail_case(self):
        d = self.decorated_func(succeed_after)
        for i in xrange(succeed_after):
            self.decorator.clock.advance(3600)
        self.assertFailure(d, TimeoutError)
    return test_fail_case

for succeed_after in xrange(MAX_RETRIES+1):
    setattr(
        RetryTestCase,
        'test_retry_succeed_on_attempt_{}'.format(succeed_after),
        _succeed_after_test_case_factory(succeed_after)
    )

for succeed_after in xrange(MAX_RETRIES+1, MAX_RETRIES+2):
    attempt_failures = succeed_after - 1
    setattr(
        RetryTestCase,
        'test_retry_fail_with_{}_attempt_failures'.format(attempt_failures),
        _fail_after_test_case_factory(succeed_after)
    )

