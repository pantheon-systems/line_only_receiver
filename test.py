from twisted.internet import defer
from retry import Retry

class Test(object):
    @Retry(4, [ValueError])
    def test(self, data):

        if data['counter'] <= 3:
            print 'Failing counter: {}'.format(data['counter'])
            data['counter'] += 1
            return defer.fail(ValueError("Fail"))
        else:
            print data['counter']
            return defer.succeed(data)

Test().test({'counter': 0})
