from twisted.internet import defer


class Command(object):
    """
    Wrap a client action into an object, that holds the values used by the
    protocol.

    _deferred: Deferred. will be fired when the result arrives.
    value: str. The value of the command sent to the server.
    """

    def __init__(self, command, value=None):
        """
        Create a command.

        Parameters:
            command: str. The name of the command
            value: str. The optional value sent along with the command.
        """
        self.command = command
        self.value = value
        self._deferred = defer.Deferred()

    def success(self, response):
        """
        Shortcut method to fire the underlying deferred.
        """

        self._deferred.callback(response)

    def fail(self, failure):
        """
        Make the underlying deferred fails.
        """
        self._deferred.errback(failure)


