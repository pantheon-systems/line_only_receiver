import wrapt

class RetryDecoratorFactory(object):
    """
    Mixin to Retry an action on a ConnectionPool

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

    delay = initialDelay
    retries = 0
    maxRetries = None
    _callID = None
    callback = None
    clock = None

    continueTrying = 1

    @wrapt.decorator()
    def __call__(self, wrapped, instance, args, kwargs):
        """
        This class should NOT be overridden
        """

        d = wrapped(*args, **kwargs)

        for _ in xrange(self.maxRetries):
            d.addErrback(self.retry, wrapped, *args, **kwargs)

        return d

    def retry(self, callback, *args, **kwargs):
        """
        Have this callback connect again, after a suitable delay.
        """
        if not self.continueTrying:
            if self.noisy:
                log.msg("Abandoning %s on explicit request" % (callback,))
            return

        if callback is None:
            raise ValueError("no callback to retry")

        self.retries += 1
        if self.maxRetries is not None and (self.retries > self.maxRetries):
            if self.noisy:
                log.msg("Abandoning %s after %d retries." %
                        (callback, self.retries))
            return

        self.delay = min(self.delay * self.factor, self.maxDelay)
        if self.jitter:
            self.delay = random.normalvariate(self.delay,
                                              self.delay * self.jitter)

        if self.noisy:
            log.msg("%s will retry in %d seconds" % (callback, self.delay,))

        def recallback():
            self._callID = None
            callback(*args, **kwargs)
        if self.clock is None:
            from twisted.internet import reactor
            self.clock = reactor
        self._callID = self.clock.callLater(self.delay, recallback)


    def stopTrying(self):
        """
        Put a stop to any attempt to reconnect in progress.
        """
        # ??? Is this function really stopFactory?
        if self._callID:
            self._callID.cancel()
            self._callID = None
        self.continueTrying = 0
        if self.callback:
            try:
                self.callback.stopConnecting()
            except error.NotConnectingError:
                pass


    def resetDelay(self):
        """
        Call this method after a successful connection: it resets the delay and
        the retry counter.
        """
        self.delay = self.initialDelay
        self.retries = 0
        self._callID = None
        self.continueTrying = 1


    def __getstate__(self):
        """
        Remove all of the state which is mutated by connection attempts and
        failures, returning just the state which describes how reconnections
        should be attempted.  This will make the unserialized instance
        behave just as this one did when it was first instantiated.
        """
        state = self.__dict__.copy()
        for key in ['callback', 'retries', 'delay',
                    'continueTrying', '_callID', 'clock']:
            if key in state:
                del state[key]
        return state
