import cPickle

from mock import patch, MagicMock
from twisted.trial import unittest

from twisted.internet import reactor
from twisted.web import client
from twisted.web.http_headers import Headers
from twisted.test.proto_helpers import StringTransport

from tx_clients.clients import http

class Matcher(object):
    """ General purpose matcher for comparing objects """
    def __init__(self, compare, obj):
        self.compare = compare
        self.obj = obj
    def __eq__(self, other):
        return self.compare(self.obj, other)

def compare_bodyProducer(self, other):
    if not type(self) == type(other):
        return False
    return cPickle.dumps(other) == cPickle.dumps(self)

class TestBasicAgent(unittest.TestCase):
    def setUp(self):
        self.patch_request = patch('tx_clients.clients.http.BasicAgent.request')
        self.mock_request = self.patch_request.start()
        self.agent = http.BasicAgent(reactor)
        self.url = 'foo'

    def test_get(self):
        self.agent.get(self.url)
        self.mock_request.assert_called_once_with('GET', self.url)

    def test_delete(self):
        self.agent.delete(self.url)
        self.mock_request.assert_called_once_with('DELETE', self.url)

    def test_post(self):
        self.agent.post(self.url)
        self.mock_request.assert_called_once_with('POST', self.url)

    def test_put(self):
        self.agent.put(self.url)
        self.mock_request.assert_called_once_with('PUT', self.url)

    def test_patch(self):
        self.agent.patch(self.url)
        self.mock_request.assert_called_once_with('PATCH', self.url)

    def test_options(self):
        self.agent.options(self.url)
        self.mock_request.assert_called_once_with('OPTIONS', self.url)

    def test_head(self):
        self.agent.head(self.url)
        self.mock_request.assert_called_once_with('HEAD', self.url)

    def test_trace(self):
        self.agent.trace(self.url)
        self.mock_request.assert_called_once_with('TRACE', self.url)

    def test_connect(self):
        self.agent.connect(self.url)
        self.mock_request.assert_called_once_with('CONNECT', self.url)

    @patch('twisted.web.client.Agent.request')
    def test_request(self, mock_request):
        self.patch_request.stop()
        args = ('GET', self.url)
        self.agent.request(*args)
        mock_request.assert_called_once_with(self.agent, *args + (None, None))
        mock_request.reset_mock()

        args = ('GET', self.url)
        data = 'foo'
        self.agent.request(*args, data=data)
        match_bodyProducer = Matcher(compare_bodyProducer, self.agent.bodyProducer(data))
        mock_request.assert_called_once_with(self.agent, *args + (None, match_bodyProducer))
        mock_request.reset_mock()

        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json')
        args = ('GET', self.url, headers)
        self.agent.request(*args, data='foo')
        match_bodyProducer = Matcher(compare_bodyProducer, self.agent.bodyProducer(data))
        mock_request.assert_called_once_with(self.agent, *args + (match_bodyProducer,))
        mock_request.reset_mock()

        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json')
        args = ('GET', self.url, headers, None)
        self.agent.request(*args)
        mock_request.assert_called_once_with(self.agent, *args)

    def tearDown(self):
        self.mock_request.reset_mock()
        # A Test may pre-emptively stop a patcher.
        try:
            self.patch_request.stop()
        except RuntimeError:
            pass


class TestBasicFileAgent(TestBasicAgent):
    def setUp(self):
        self.patch_request = patch('tx_clients.clients.http.BasicFileAgent.request')
        self.mock_request = self.patch_request.start()
        self.agent = http.BasicFileAgent(reactor)
        self.url = 'foo'


class TestBasicJSONAgent(TestBasicAgent):
    def setUp(self):
        self.patch_request = patch('tx_clients.clients.http.BasicJSONAgent.request')
        self.mock_request = self.patch_request.start()
        self.agent = http.BasicJSONAgent(reactor)
        self.url = 'foo'

    @patch('twisted.web.client.Agent.request')
    def test_request(self, mock_request):
        self.patch_request.stop()
        args = ('GET', self.url)
        self.agent.request(*args)
        mock_request.assert_called_once_with(self.agent, *args + (None, None))
        mock_request.reset_mock()

        args = ('GET', self.url)
        data = 'foo'
        self.agent.request(*args, data=data)
        match_bodyProducer = Matcher(compare_bodyProducer, self.agent.bodyProducer(data))
        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json; charset=utf-8')
        mock_request.assert_called_once_with(self.agent, *args + (headers, match_bodyProducer))
        mock_request.reset_mock()

        args = ('GET', self.url, None, 'foo')
        self.agent.request(*args)
        match_bodyProducer = Matcher(compare_bodyProducer, self.agent.bodyProducer(args[-1]))
        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json; charset=utf-8')
        mock_request.assert_called_once_with(self.agent, *args[:2] + (headers, match_bodyProducer))
        mock_request.reset_mock()

        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json')
        args = ('GET', self.url, headers)
        self.agent.request(*args, data='foo')
        match_bodyProducer = Matcher(compare_bodyProducer, self.agent.bodyProducer(data))
        mock_request.assert_called_once_with(self.agent, *args + (match_bodyProducer,))
        mock_request.reset_mock()

        headers = Headers()
        headers.addRawHeader('Content-Type', 'application/json')
        args = ('GET', self.url, headers, None)
        self.agent.request(*args)
        mock_request.assert_called_once_with(self.agent, *args)



class TestHttp(unittest.TestCase):
    def test_dict_to_raw_headers(self):
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        headers_obj = http.dict_to_raw_headers(headers)
        for header in headers:
            self.assertEquals(headers_obj.getRawHeaders(header), [headers[header]])

class TestBasicResponse(unittest.TestCase):
    def setUp(self):
        self.version = 'mock version'
        self.code = 'mock code'
        self.phrase = 'mock phrase'
        self.headers = 'mock headers'
        self.body = 'foo'
        self.length = len(self.body)
        self.transport = StringTransport()
        self.stub_response = client.Response(
            self.version,
            self.code,
            self.phrase,
            self.headers,
            self.transport
        )
        self.stub_response.length = self.length
        self.stub_response._bodyDataReceived(self.body)
        self.stub_response._bodyDataFinished()

    def test_basic_response_method_HEAD(self):
        response_wrapper = http.BasicResponse()
        wrapped_response = response_wrapper(self.stub_response, 'HEAD').result
        self.assertEquals(wrapped_response, response_wrapper)
        self.assertEquals(wrapped_response.method, response_wrapper.method)
        self.assertEquals(wrapped_response.version, self.stub_response.version)
        self.assertEquals(wrapped_response.code, self.stub_response.code)
        self.assertEquals(wrapped_response.phrase, self.stub_response.phrase)
        self.assertEquals(wrapped_response.headers, self.stub_response.headers)
        self.assertEquals(wrapped_response.length, self.stub_response.length)
        self.assertEquals(wrapped_response.body, None)

    def test_basic_response_no_body_code(self):
        response_wrapper = http.BasicResponse()
        self.stub_response.code = 204
        wrapped_response = response_wrapper(self.stub_response, 'POST').result

        self.assertEquals(wrapped_response, response_wrapper)
        self.assertEquals(wrapped_response.method, response_wrapper.method)
        self.assertEquals(wrapped_response.version, self.stub_response.version)
        self.assertEquals(wrapped_response.code, self.stub_response.code)
        self.assertEquals(wrapped_response.phrase, self.stub_response.phrase)
        self.assertEquals(wrapped_response.headers, self.stub_response.headers)
        self.assertEquals(wrapped_response.length, self.stub_response.length)
        self.assertEquals(wrapped_response.body, None)

        self.stub_response.code = 304
        wrapped_response = response_wrapper(self.stub_response, 'POST').result

        self.assertEquals(wrapped_response, response_wrapper)
        self.assertEquals(wrapped_response.method, response_wrapper.method)
        self.assertEquals(wrapped_response.version, self.stub_response.version)
        self.assertEquals(wrapped_response.code, self.stub_response.code)
        self.assertEquals(wrapped_response.phrase, self.stub_response.phrase)
        self.assertEquals(wrapped_response.headers, self.stub_response.headers)
        self.assertEquals(wrapped_response.length, self.stub_response.length)
        self.assertEquals(wrapped_response.body, None)

    def test_basic_response_GET_200(self):
        response_wrapper = http.BasicResponse()
        self.stub_response.code = 200
        wrapped_response = response_wrapper(self.stub_response, 'GET').result

        self.assertEquals(wrapped_response, response_wrapper)
        self.assertEquals(wrapped_response.method, response_wrapper.method)
        self.assertEquals(wrapped_response.version, self.stub_response.version)
        self.assertEquals(wrapped_response.code, self.stub_response.code)
        self.assertEquals(wrapped_response.phrase, self.stub_response.phrase)
        self.assertEquals(wrapped_response.headers, self.stub_response.headers)
        self.assertEquals(wrapped_response.length, self.stub_response.length)
        self.assertEquals(wrapped_response.body, self.body)

