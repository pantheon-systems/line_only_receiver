import random
from twisted.python import log

import wrapt

class Retry(object):
    """
    A decorator factory to create retry decorators, which retry a command on a connection pool

    Note that clients should call my resetDelay method after they have
    connected successfully.

    @ivar maxDelay: Maximum number of seconds between connection attempts.
    @ivar initialDelay: Delay for the first reconnection attempt.
    @ivar factor: A multiplicitive factor by which the delay grows
    @ivar jitter: Percentage of randomness to introduce into the delay length
        to prevent stampeding.
    @ivar clock: The clock used to schedule reconnection. It's mainly useful to
        be parametrized in tests. If the factory is serialized, this attribute
        will not be serialized, and the default value (the reactor) will be
        restored when deserialized.
    @type clock: L{IReactorTime}
    @ivar maxRetries: Maximum number of consecutive unsuccessful connection
        attempts, after which no further connection attempts will be made. If
        this is not explicitly set, no maximum is applied.
    """
    maxDelay = 3600
    initialDelay = 1.0
    # Note: These highly sensitive factors have been precisely measured by
    # the National Institute of Science and Technology.  Take extreme care
    # in altering them, or you may damage your Internet!
    # (Seriously: <http://physics.nist.gov/cuu/Constants/index.html>)
    factor = 2.7182818284590451 # (math.e)
    # Phi = 1.6180339887498948 # (Phi is acceptable for use as a
    # factor if e is too large for your application.)
    jitter = 0.11962656472 # molar Planck constant times c, joule meter/mole

    noisy = True
    delay = initialDelay
    retries = 0
    maxRetries = None
    _callID = None
    clock = None
    _wrapped = None

    def __init__(self, maxRetries, handled_exceptions):
        """
        Creates Retry object

        handled_exceptions is list of exceptions to trigger a Retry
        """

        self.maxRetries = maxRetries
        self.handled_exceptions = handled_exceptions

    @wrapt.decorator()
    def __call__(self, wrapped, instance, args, kwargs):
        """
        This class should NOT be overridden
        """

        #self._wrapped = wrapped.__wrapped__

        print 'wrapped {}'.format(dir(wrapped))
        print 'instance {}'. format(dir(instance.__class__))
        print 'self {}'.format(dir(self))
        self._wrapped = getattr(instance.__class__, wrapped.__name__)
        print dir(self._wrapped)
        self._instance = instance
        d = wrapped(*args, **kwargs)
        print 'defer', d

        for _ in xrange(self.maxRetries):
            print 'add retry'
            d.addErrback(self.retry, *args, **kwargs)

        return d

    def retry(self, failure, *args, **kwargs):
        """
        Have this command connect again, after a suitable delay.
        """

        # Only retry for hanlded exceptions
        t = failure.trap(*self.handled_exceptions)

        if t not in self.handled_exceptions:
            print 'not trapped', failure
            return failure

        self.retries += 1

        self.delay = min(self.delay * self.factor, self.maxDelay)
        if self.jitter:
            self.delay = random.normalvariate(self.delay,
                                              self.delay * self.jitter)

        if self.noisy:
            print("Running command {} in {} seconds. Retry {}/{}".format(
                self._wrapped,
                self.delay,
                self.retries,
                self.maxRetries)
            )

        def recommand():
            self._callID = None
            return self._wrapped(self._instance, *args, **kwargs)

        if self.clock is None:
            from twisted.internet import reactor
            self.clock = reactor
        self._callID = self.clock.callLater(self.delay, recommand)

        return self._callID
