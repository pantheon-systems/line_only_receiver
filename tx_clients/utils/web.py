# pylint: disable=unused-argument

import base64
import cStringIO
import json

from zope.interface import implements

from twisted.web import client
from twisted.web.iweb import IBodyProducer
from twisted.internet.task import cooperate


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
        """ Must NOT call registerProducer on the consumer """
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


class AsyncJSON(object):
    """ See: twisted.internet.interfaces.IPushProducer """
    def __init__(self, value):
        self.value = value
        self._consumer = None
        self._iterable = None
        self._task = None

    def beginProducing(self, consumer):
        """ See: twisted.internet.interfaces.IConsumer """
        self._consumer = consumer
        self._iterable = json.JSONEncoder().iterencode(self.value)
        self._consumer.registerProducer(self, True)
        self._task = cooperate(self._produce())
        d = self._task.whenDone()
        d.addBoth(self._unregister)
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

    def _unregister(self, passthrough):
        self._consumer.unregisterProducer()
        return passthrough


def generate_basic_authorization_string(user, password):
    # Basic Auth Credentials
    base64string = base64.encodestring('%s:%s' % (user, password))[:-1]
    return "Basic %s" % base64string

