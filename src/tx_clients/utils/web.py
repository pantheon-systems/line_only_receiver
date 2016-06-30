import base64
import cStringIO
import json
import warnings

from zope.interface import implements

from twisted.web import client
from twisted.web.iweb import IBodyProducer
from twisted.internet import defer, protocol
from twisted.internet.task import cooperate
from twisted.web.http import PotentialDataLoss


class StringBodyProducer(client.FileBodyProducer):
    """ See: twisted.web.client.FileBodyProducer """
    def __init__(self, string, *args, **kwargs):
        """ The FileBodyProducer accepts file like objects """
        client.FileBodyProducer.__init__(self, cStringIO.StringIO(string), *args, **kwargs)


class JSONBodyProducer(object):
    """ See: twisted.web.iweb.IBodyProducer """
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = client.UNKNOWN_LENGTH
        self._consumer = None
        self._iterable = None
        self._task = None

    def startProducing(self, consumer):
        self._consumer = consumer
        self._iterable = json.JSONEncoder().iterencode(self.body)
        self._task = cooperate(self._produce())
        d = self._task.whenDone()
        return d

    def pauseProducing(self):
        self._task.pause()

    def resumeProducing(self):
        self._task.resume()

    def stopProducing(self):
        self._task.stop()

    def _produce(self):
        for chunk in self._iterable:
            self._consumer.write(chunk)
            yield None


# Ported from twisted.web.client version Twisted 16.2.0
class _ReadBodyProtocol(protocol.Protocol):
    """
    Protocol that collects data sent to it.
    This is a helper for L{IResponse.deliverBody}, which collects the body and
    fires a deferred with it.
    """

    def __init__(self, status, message, deferred):
        """
        @param status: Status of L{IResponse}
        @ivar status: L{int}
        @param message: Message of L{IResponse}
        @type message: L{bytes}
        @param deferred: deferred to fire when response is complete
        @type deferred: L{Deferred} firing with L{bytes}
        """
        self.deferred = deferred
        self.status = status
        self.message = message
        self.dataBuffer = []


    def dataReceived(self, data):
        """
        Accumulate some more bytes from the response.
        """
        self.dataBuffer.append(data)


    def connectionLost(self, reason=protocol.connectionDone):
        """
        Deliver the accumulated response bytes to the waiting L{Deferred}, if
        the response body has been completely received without error.
        """
        if reason.check(client.ResponseDone):
            self.deferred.callback(b''.join(self.dataBuffer))
        elif reason.check(PotentialDataLoss):
            self.deferred.errback(
                client.PartialDownloadError(
                    self.status,
                    self.message,
                    b''.join(self.dataBuffer)
                )
            )
        else:
            self.deferred.errback(reason)


# Ported from twisted.web.client version Twisted 16.2.0
def readBody(response):
    """
    Get the body of an L{IResponse} and return it as a byte string.
    This is a helper function for clients that don't want to incrementally
    receive the body of an HTTP response.
    @param response: The HTTP response for which the body will be read.
    @type response: L{IResponse} provider
    @return: A L{Deferred} which will fire with the body of the response.
        Cancelling it will close the connection to the server immediately.
    """
    def cancel(deferred):
        """
        Cancel a L{readBody} call, close the connection to the HTTP server
        immediately, if it is still open.
        @param deferred: The cancelled L{defer.Deferred}.
        """
        abort = getAbort()
        if abort is not None:
            abort()
    d = defer.Deferred(cancel)
    proto = _ReadBodyProtocol(response.code, response.phrase, d)
    def getAbort():
        return getattr(proto.transport, 'abortConnection', None)

    response.deliverBody(proto)

    if proto.transport is not None and getAbort() is None:
        warnings.warn(
            'Using readBody with a transport that does not have an '
            'abortConnection method',
            category=DeprecationWarning,
            stacklevel=2
        )

    return d


def generate_basic_authorization_string(user, password):
    # Basic Auth Credentials
    base64string = base64.encodestring('%s:%s' % (user, password))[:-1]
    return "Basic %s" % base64string

