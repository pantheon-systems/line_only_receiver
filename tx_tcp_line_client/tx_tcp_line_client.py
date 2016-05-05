from collections import deque

from twisted.python import log
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
        @param timeOut: the timeout to wait before detecting that the
            connection is dead and close it. It's expressed in seconds.
        @type timeOut: C{int}
        """
        self.persistentTimeOut = timeOut
        self.timeOut = None

    def timeoutConnection(self):
        """
        Close the connection in case of timeout.
        """
        log.error('Notification-service: connection timed-out')

        self.transport.loseConnection()

    def lineReceived(self, line):
        """
        Receive line commands from the server.
        """
        self.setTimeout(None)

        # Only print if failed response
        if line != 'OK':
          log.error("Notification-service: Got failed response: {}".format(line))

    def sendLine(self, line):
        """
        Override sendLine method
        """

        # Set timeout if there isn't already one running
        if not self.timeOut:
           self.setTimeout(self.persistentTimeOut)

        if not isinstance(line, str):
            return fail(ClientError(
                "Invalid type for value: %s, expecting a string" %
                (type(line),)))
        LineOnlyReceiver.sendLine(self, line)
        cmdObj = Command(line)
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
        mc_pool = LineOnlyReceiverPool(addr, maxClients=20)

        d = mc_pool.get('cached-data')

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

