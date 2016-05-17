from txconnpool.pool import PooledClientFactory, Pool

from tx_clients.protocols import LineProtocol
from tx_clients.utils import Retry
from tx_clients.exceptions import TimeoutError


class PooledLineProtocol(LineProtocol):
    """
    A LineProtocol that will notify a connectionPool that it is ready
    to accept requests.
    """

    def connectionMade(self):
        """
        Notify our factory that we're ready to accept connections.
        """
        LineProtocol.connectionMade(self)

        self.factory.connectionPool.clientFree(self)

        if self.factory.deferred is not None:
            self.factory.deferred.callback(self)
            self.factory.deferred = None


class PooledLineClientFactory(PooledClientFactory):
    protocol = PooledLineProtocol


class LineClientPool(Pool):
    """
    A LineOnlyReceiver client which is backed by a pool of connections.

    Usage Example::
        from twisted.internet.address import IPv4Address
        from txclients import LineClientPool

        addr = IPv4Address('TCP', '127.0.0.1', 11211)
        pool = LineClientPool(addr, maxClients=20)

        d = pool.sendLine('foo')

        def responseHandler(response):
            print 'Yay, we got a response', response

        def failureHandleri(failure):
            print 'Something bad happend', failure


        d.addCallbacks(responeHandler, failureHandler)
    """
    clientFactory = PooledLineClientFactory

    @Retry(3, (TimeoutError,), maxDelay=3)
    def send(self, data):
        """
        See L{twisted.protocols.basic.LineOnlyReceiver.get}.
        """
        return self.performRequest('sendLine', data)

