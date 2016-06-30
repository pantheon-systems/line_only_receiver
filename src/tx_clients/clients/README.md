# Clients
A collection of clients and helpers written using the twisted framework

## Http Client
This http client provides wrappers around [twisted.web.client.Agent][]. These wrappers provide a "requests" like interface that satisfies a majority of use cases. Consider this library a bicycle with training wheels. For more advanced use cases use the Twisted Agent directly.

### Anatomy of an Agent
See: [twisted.web.iweb.IAgent][]  

An Agent is passed a reactor and optionally a context factory and connection pool. 

See: [twisted.web.client.WebClientContextFactory][]  
See: [twisted.web._newclient.HTTP11ClientProtocol][] 

An Agent makes requests with a HTTP verb, and url. You can optionally provide headers and a body producer. 

See: [twisted.web.http_headers.Headers][]  
See: [twisted.web.iweb.IBodyProducer][] 

### Using an Agent
You can use the twisted agent directly [Twisted 12.2.0 Client Documentation][].
Use of [twisted.web.client.getPage][] and [twisted.web.client.downloadPage][] is __strongly__ discouraged. It uses a legacy API and has many shortcomings.

Twisted 12.2.0 provides the following Agents

* [twisted.web.client.Agent][]
* [twisted.web.client.ProxyAgent][]
* [twisted.web.client.CookieAgent][]
* [twisted.web.client.ContentDecoderAgent][]
* [twisted.web.client.RedirectAgent][]

### Using Agent Helpers
For convenience the provided helpers are subclasses of [twisted.web.client.Agent][] and may be easier to use. The interface is similar to using the requests library.

NOTE: Helpers have only been created for [twisted.web.client.Agent][] and not other Agent classes. Each agent may have a slightly different __init__ method and process for making requests. Id like to turn the helpers into a Mixin that wraps a [twisted.web.iweb.IAgent][] but we need to upgrade Twisted >= 15.0.0.

#### Whats different?
HTTP Verbs are mapped to methods on the Agent.

    agent.request('GET', url) == agent.get(url)

A bodyProducer has been set upon each agent helper. This producer will wrap what is passed into data.

__BasicAgent__

    # BasicStringAgent.bodyProducer is a tx_clients.utils.web.StringBodyProducer
    # This makes it convenient to send strings as the body of the request
    data = 'foo'
    d = agent.post(url, data=data)

__BasicFileAgent__

    # BasicFileAgent.bodyProducer is a twisted.web.client.FileBodyProducer
    # This makes it convenient to send file like objects as the body of the request. It can be used to stream open files.
    with open('/path/to/file.txt', 'r') as fd:
        d = agent.post(url, data=fd)

__BasicJSONAgent__

    # BasicJSONAgent.bodyProducer is a tx_clients.utils.web.JSONBodyProducer
    # This makes it convenient to send JSONable python objects. Note: Default encoding is utf-8
    data = {'foo': 'bar'}
    d = agent.post(url, data=data)
    # The content-type will also be set automatically.


### Agent Invocation
Agents can be invoked both synchronously and asynchronously.

__Asynchronous Example__

    from twisted.internet import reactor
    from twisted.web import client

    from tx_clients.clients import http

    # Adding a pool is optional. A non persistent connection pool is created by default
    pool = client.HTTPConnectionPool(reactor)
    agent = http.BasicAgent(reactor, pool=pool)
    d = agent.get('https://api.live.getpantheon.com:8443')

    def print_response(response):
        print response.body

    d.addCallback(print_response)

    def cbShutdown(response):
        reactor.stop()
    d.addBoth(cbShutdown)

    reactor.run()

__Inline Callbacks Example__ - Also Asynchronous but marginally slower.

    from twisted.internet import reactor, defer
    from twisted.web import client

    from tx_clients.clients import http

    @defer.inlineCallbacks
    def main():
        # Adding a pool is optional. A non persistent connection pool is created by default
        pool = client.HTTPConnectionPool(reactor)
        agent = http.BasicAgent(reactor, pool=pool)
        response = yield agent.get('https://api.live.getpantheon.com:8443')
        print response.body
        reactor.stop()

    main()
    reactor.run()

__Synchrnous Example__ - The Synchronous example requires [Crochet 1.4.0][] (Crochet 1.5.0 requires Twisted >= 15.0.0)

    from twisted.internet import reactor
    from twisted.web import client

    from tx_clients.clients import http
    
    from crochet import setup, wait_for, TimeoutError
    setup()

    # Adding a pool is optional. A non persistent connection pool is created by default
    pool = client.HTTPConnectionPool(reactor)
    agent = http.BasicAgent(reactor, pool=pool)
    try:
        response = wait_for(timeout=1)(agent.get)('https://api.live.getpantheon.com:8443')
        print response.body
    except TimeoutError:
        print 'Request Timed Out'

## Line Client
__TODO: DEPRECATE__ The notification-service (i.e. pubsub proxy) also has an http interface. We should discontinue use of the line protocol to the notification-service and instead use the http client below.

A connection pooled client that speaks a simple line protocol. This protocol diverges slightly from the twisted implementation
to adhere to the semantics of the notification-service (google pub/sub proxy) sidecar.

The line client has a dependency upon txconnpool which is an older implementation of connection pooling.


[twisted.web.client.Agent]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L1096
[twisted.web.client.ProxyAgent]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L1211
[twisted.web.client.CookieAgent]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L1325
[twisted.web.client.ContentDecoderAgent]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L1463
[twisted.web.client.RedirectAgent]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L1526
[twisted.web._newclient.HTTP11ClientProtocol]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/_newclient.py#L1190
[twisted.web.iweb.IAgent]: https://github.com/twisted/twisted/blob/twisted-16.2.0/twisted/web/iweb.py#L633
[Twisted 12.2.0 Client Documentation]: https://twistedmatrix.com/documents/12.2.0/web/howto/client.html
[twisted.web.iweb.IBodyProducer]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/iweb.py#L633
[twisted.web.client.WebClientContextFactory]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L664
[twisted.web.client.getPage]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L611
[twisted.web.client.downloadPage]: https://github.com/twisted/twisted/blob/twisted-12.2.0/twisted/web/client.py#L627
[Crochet 1.4.0]: https://github.com/itamarst/crochet/tree/1.4.0
[twisted.web.http_headers.Headers]: https://github.com/twisted/twisted/blob/twisted-12.3.0/twisted/web/http_headers.py#L105
