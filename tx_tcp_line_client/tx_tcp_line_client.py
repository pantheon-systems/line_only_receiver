from collections import deque

from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.defer import Deferred, fail, TimeoutError

from txconnpool.pool import PooledClientFactory, Pool

class ClientError(Exception):
    """
    Error caused by an invalid client call.
    """

class ResponseError(Exception):
    """
    Error caused by a bad response
    """


class Command(object):
    """
    Wrap a client action into an object, that holds the values used in the
    protocol.
    @ivar _deferred: the L{Deferred} object that will be fired when the result
        arrives.
    @type _deferred: L{Deferred}
    @ivar command: name of the command sent to the server.
    @type command: C{str}
    """

    def __init__(self, command):
        """
        Create a command.
        @param command: the name of the command.
        @type command: C{str}
        """
        self.command = command
        self._deferred = Deferred()

    def success(self, value):
        """
        Shortcut method to fire the underlying deferred.
        """

        self._deferred.callback(value)


    def fail(self, error):
        """
        Make the underlying deferred fails.
        """
        self._deferred.errback(error)


class _PooledLineOnlyReceiver(LineOnlyReceiver, TimeoutMixin):
    """
    A LineOnlyReceiver that will notify a connectionPool that it is ready
    to accept requests.
    """
    factory = None

    def __init__(self, timeOut=60):
        """
        Create the protocol.
        @ivar _current: current list of requests waiting for an answer from the
            server.
        @type _current: C{deque} of L{Command}

        @param timeOut: the timeout to wait before detecting that the
            connection is dead and close it. It's expressed in seconds.
        @type timeOut: C{int}
        """
        self._queue = deque()
        self.persistentTimeOut = timeOut
        self.timeOut = None

    def _cancelCommands(self, reason):
        """
        Cancel all the outstanding commands, making them fail with C{reason}.
        """
        while self._queue:
            cmd = self._queue.popleft()
            cmd.fail(reason)

    def timeoutConnection(self):
        """
        Close the connection in case of timeout.
        """
        self._cancelCommands(TimeoutError("Connection timeout"))
        self.transport.loseConnection()

    def connectionLost(self, reason):
        """
        Cause any outstanding commands to fail.
        """
        self._disconnected = True
        self._cancelCommands(reason)
        LineReceiver.connectionLost(self, reason)

    def cmd_OK(self):
        """
        The last command has been completed.
        """
        self._queue.popleft().success(True)

    def cmd_UNKNOWN(self, reason):
        self._queue.popleft().fail(reason)

    def lineReceived(self, line):
        """
        Receive line commands from the server.
        """
        self.resetTimeout()
        token = line.split(" ", 1)[0]
        # First manage standard commands without space
        cmd = getattr(self, "cmd_%s" % (token,), None)
        if cmd is not None:
            args = line.split(" ", 1)[1:]
            if args:
                cmd(args[0])
            else:
                cmd()
        else:
            # Then manage commands with space in it
            line = line.replace(" ", "_")
            cmd = getattr(self, "cmd_%s" % (line,), None)
            if cmd is not None:
                cmd()
            else:
                # Increment/Decrement response
                cmd = self._queue.popleft()
                cmd_UNKNOWN("Unknown response received: {0}".format(val))

        if not self._queue:
            # No pending request, remove timeout
            self.setTimeout(None)

    def sendLine(self, line):
        """
        Override sendLine method
        """

        # Set timeout if there isn't already one running
        if not self._queue:
           self.setTimeout(self.persistentTimeOut)

        if not isinstance(line, str):
            return fail(ClientError(
                "Invalid type for value: %s, expecting a string" %
                (type(line),)))
        LineOnlyReceiver.sendLine(self, line)
        cmdObj = Command(line)
        self._queue.append(cmdObj)
        return cmdObj._deferred

    def connectionMade(self):
        """
        Notify our factory that we're ready to accept connections.
        """
        LineOnlyReceiver.connectionMade(self)

        self.factory.connectionPool.clientFree(self)

        if self.factory.deferred is not None:
            self.factory.deferred.callback(self)
            self.factory.deferred = None


class _LineOnlyReceiverClientFactory(PooledClientFactory):
    """
    L{PooledClientFactory} that uses L{_PooledLineOnlyReceiver}
    """
    protocol = _PooledLineOnlyReceiver


class LineOnlyReceiverPool(Pool):
    """
    A LineOnlyReceiver client which is backed by a pool of connections.

    Usage Example::
        from twisted.internet.address import IPv4Address
        from txconnpool.line_receiver import LineOnlyReceiverPool

        addr = IPv4Address('TCP', '127.0.0.1', 11211)
        pool = LineOnlyReceiverPool(addr, maxClients=20)

        d = pool.sendLine('cached-data')

        def gotCachedData(data):
            flags, value = data
            if value:
                print 'Yay, we got a cache hit'
            else:
                print 'Boo, it was a cache miss'

        d.addCallback(gotCachedData)
    """
    clientFactory = _LineOnlyReceiverClientFactory

    def sendLine(self, data):
        """
        See L{twisted.protocols.basic.LineOnlyReceiver.get}.
        """
        return self.performRequest('sendLine', data)

