import random
import wrapt

from twisted.python import log
from twisted.internet import task

class Retry(object):
    """
    A class decorator to retry a command on a connection pool. Retry attempts
    use an exponential backoff algorithm. Commands MUST return a deferred
    object.

    @ivar factor: A multiplicitive factor by which the delay grows
    @ivar jitter: Percentage of randomness to introduce into the delay length
        to prevent stampeding.
    @ivar clock: The clock used to schedule reconnection. It's mainly useful to
        be parametrized in tests. If the factory is serialized, this attribute
        will not be serialized, and the default value (the reactor) will be
        restored when deserialized.
    @type clock: L{IReactorTime}
    """
    # Note: These highly sensitive factors have been precisely measured by
    # the National Institute of Science and Technology.  Take extreme care
    # in altering them, or you may damage your Internet!
    # (Seriously: <http://physics.nist.gov/cuu/Constants/index.html>)
    factor = 2.7182818284590451 # (math.e)
    # Phi = 1.6180339887498948 # (Phi is acceptable for use as a
    # factor if e is too large for your application.)
    jitter = 0.11962656472 # molar Planck constant times c, joule meter/mole

    noisy = True
    clock = None
    _wrapped = None

    def __init__(self, maxRetries, handled_exceptions, maxDelay=300, initialDelay=0.5):
        """
        Creates Retry object

        maxDelay: Maximum number of seconds between connection attempts.
        handled_exceptions: A list of exceptions that will trigger a retry if
            thrown.
        initialDelay: Delay for the first reconnection attempt.
        maxRetries: Maximum number of consecutive unsuccessful connection
            attempts, after which no further connection attempts will be made. If
            this is not explicitly set, no maximum is applied.
        """

        self.maxRetries = maxRetries
        self.handled_exceptions = handled_exceptions
        self.maxDelay = maxDelay
        self.initialDelay = initialDelay

    @wrapt.decorator()
    def __call__(self, wrapped, instance, args, kwargs):
        """
        This class should NOT be overridden
        """

        self._wrapped = wrapped
        d = wrapped(*args, **kwargs)

        delay = random.normalvariate(
            self.initialDelay,
            self.initialDelay * self.jitter
        )
        d.addErrback(self.retry, 1, delay, *args, **kwargs)
        return d

    def retry(self, failure, retry, delay, *args, **kwargs):
        """
        Have this command connect again, after a suitable delay.
        """

        # Only retry for hanlded exceptions
        t = failure.trap(*self.handled_exceptions)

        if t not in self.handled_exceptions:
            return failure

        if self.noisy:
            print("Retrying function {} in {} seconds {}/{}".format(
                self._wrapped,
                delay,
                retry,
                self.maxRetries)
            )

        if self.clock is None:
            # This is necessary to allow testing by overwriting the clock
            from twisted.internet import reactor
            self.clock = reactor
        _new_attempt = task.deferLater(self.clock, delay, self._wrapped, *args, **kwargs)

        if retry < self.maxRetries:
            delay = min(delay * self.factor, self.maxDelay)
            if self.jitter:
                delay = random.normalvariate(
                    delay,
                    delay * self.jitter
                )
            _new_attempt.addErrback(self.retry, retry+1, delay, *args, **kwargs)

        return _new_attempt

