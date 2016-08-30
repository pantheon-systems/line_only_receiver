# pylint: disable=protected-access, too-many-arguments, too-many-instance-attributes
from collections import OrderedDict

from zope.interface import implements

from twisted.web import client, http
from twisted.web.iweb import IResponse
from twisted.internet import defer
from twisted.web.http_headers import Headers
from twisted.test.proto_helpers import StringTransport


from tx_clients.utils.web import (
    JSONBodyProducer,
    StringBodyProducer
)


# A dictionary is insufficient for supplying headers since a header may be
# sent multiple times. Dont be lazy, Create a Headers object whenever possible
def dict_to_raw_headers(dict_headers):
    return Headers({k: [v] for k, v in dict_headers.viewitems()})


class BasicResponse(object):
    """ Return's a deferred that fires when the body is received
    The body is attached as a parameter on the BasicResponse object
    This is a helper which implements the twisted IResponse interface.
    This wrapper provides an asynchronous way of waiting for the body.

    An alternative is to read the response seperately the response object will
    not be available to the final callback. Only the contents of the body.:
        agent = Agent(reactor)
        d = agent.request('GET', 'https://google.com')
        d.addCallback(readBody)
    """
    implements(IResponse)

    def __init__(self):
        """ BasicResponse objects wrap twisted.web.client.iweb.IResponse """
        self._response = None
        self.method = None
        self.version = None
        self.code = None
        self.phrase = None
        self.headers = None
        self.length = None
        self.body = None

    def __call__(self, response, method):
        """
        response See: twisted.web.client.iweb.IResponse
        method: http verb
        """
        self._response = response
        self.method = method
        self.version = response.version
        self.code = response.code
        self.phrase = response.phrase
        self.headers = response.headers
        self.length = response.length
        self.body = None
        return self.deliverBody()

    def cbAttachBody(self, body):
        # Attach the body and return the BasicResponse object
        self.body = body
        # Should we log a warning if the length sent by the server mismatches?
        self.length = len(body)
        return self

    def deliverBody(self):
        if self._response.code in http.NO_BODY_CODES or self.method == 'HEAD':
            return defer.succeed(self)
        d = client.readBody(self._response)
        d.addCallback(self.cbAttachBody)
        return d


class BasicAgent(client.Agent):
    """ Returns a Deferred which contains a BasicResponse
    Asynchronous HTTP Client Helper which makes some assumptions to satisfy the
    majority of use cases. See: twisted.web.iweb.IAgent for the details of
    the Agent interface.

    - The deferred object waits for headers and the body to be delivered
    before firing. It's result MUST be a Response object.
    - The data attached to the request MUST be a string. Unicode is never valid.
    The producer on the client will wrap the string.
    - Headers MUST be a twisted.web.client.Headers object
    - All semantics of the underlying agent also apply
        - See: twisted.web.iweb.IAgent
    - Provides a "requests" like interface

    If your use case diverges from this pattern then you should probably be using
    the twisted Agent directly. See Documentation:
    https://twistedmatrix.com/documents/12.2.0/web/howto/client.html

    Usage:
        def cbResponse(response):
            # Handle successful response
            print response
            return response
        def ebFailure(failure):
            # Handle failure while generating the response
            print failure
            return failure
        client = BasicAgent(reactor)
        d = client.get("https://127.0.0.1:8443/my/path")
        d.addCallbacks(cbResponse, cbErrback)
        return d
    """
    bodyProducer = StringBodyProducer

    def request(self, method, uri, headers=None, data=None):
        """ Returns an imutable Response object when the body is availabele """
        producer = None
        if data is not None:
            producer = self.bodyProducer(data)

        d = client.Agent.request(self, method, uri, headers, producer)
        d.addCallback(BasicResponse(), method)
        return d

    def get(self, *args, **kwargs):
        return self.request('GET', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('DELETE', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request('PUT', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('PATCH', *args, **kwargs)

    def options(self, *args, **kwargs):
        return self.request('OPTIONS', *args, **kwargs)

    def head(self, *args, **kwargs):
        return self.request('HEAD', *args, **kwargs)

    def trace(self, *args, **kwargs):
        return self.request('TRACE', *args, **kwargs)

    def connect(self, *args, **kwargs):
        return self.request('CONNECT', *args, **kwargs)


class BasicFileAgent(BasicAgent):
    """
    See: BasicHTTPClient

    - The basic File Agent asynchronously sends data from a file like object
    - Automatically sets transfer encoding to chunked
    """
    bodyProducer = client.FileBodyProducer


class BasicJSONAgent(BasicAgent):
    """
    See: BasicHTTPClient

    - The basic JSON Agent asynchronously encodes and sends data as json
    - Automatically sets the content-type
    - Automatically sets transfer encoding to chunked
    """
    bodyProducer = JSONBodyProducer

    def request(self, method, uri, headers=None, data=None):
        if data is not None:
            if headers is None:
                headers = Headers()
            headers.removeHeader('Content-Type')
            headers.addRawHeader('Content-Type', 'application/json; charset=utf-8')
        return BasicAgent.request(self, method, uri, headers, data)


def stub_agent_factory(agent_cls):
    """
    The stub agent factory returns a stub agent that is a subclass of the
    base class that is passed into the function.

    This stub agent is a tool which can be used for unit tests as well as
    generating contract tests. Gateway unit-tests should never perform any live
    requests and so a stub agent should be used. For integration testing use a
    live agent.

    The stub agent collects requests in the order in which they are made. This
    allows easy access to iteratively respond to the requests in an ordered manner.

    Requests can only have one response or failure instance applied so a queue
    is constructed to track which requests have already been acted upon.

    The second tool is "live replay". All recorded requests are performed on a
    live agent. The response to each request is stored in a live_request_history.
    This is useful for recording the current state and behaivor of an external
    api. The live replay is a good tool for generating mocks or scheama but
    again it should not be used for integration testing.
    """
    class StubBasicAgent(agent_cls):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.request_history = OrderedDict()
            self.request_queue = OrderedDict()
            self.live_request_history = OrderedDict()

        @defer.inlineCallbacks
        def replay_live(self):
            """
            Performs live requests with a live agent. Requires networking.
            This is a tool that is useful for generating live responses for
            requests that have been recorded by the stub agent.

            Live requests will only be performed once per request.
            """
            live_agent = agent_cls(*self.args, **self.kwargs)
            for stub_response in self.request_history.viewkeys():
                if stub_response not in self.live_request_history:
                    args, kwargs = self.request_history[stub_response]
                    try:
                        live_response = yield live_agent.request(*args, **kwargs)
                    except Exception as e:  # pylint: disable=broad-except
                        live_response = e
                    self.live_request_history[stub_response] = ((args, kwargs), live_response)
            yield defer.succeed(None)

        def request(self, *args, **kwargs):
            d_response = defer.Deferred()
            self.request_history[d_response] = (args, kwargs)
            self.request_queue[d_response] = (args, kwargs)
            return d_response

        @staticmethod
        def stub_response(method, version, code, phrase, headers, body):
            """ Build a stub response object. """
            transport = StringTransport()
            res = client.Response(version, code, phrase, headers, transport)
            res._bodyDataReceived(body)
            res._bodyDataFinished()
            return BasicResponse()(res, method).result

        def respond(self, version, code, phrase, headers, body):
            """ Respond to requests in FIFO order. """
            d_response, params = self.request_queue.popitem(False)
            args, kwargs = params
            method = args[0] if args else kwargs['method']
            response = self.stub_response(method, version, code, phrase, headers, body)
            d_response.callback(response)

        def fail(self, reason):
            """
            Fail requests in FIFO order.
            reason Exception. An exception instance to pass to the errback chain.
            """
            d_response, _ = self.request_queue.popitem(False)
            d_response.errback(reason)

    return StubBasicAgent


