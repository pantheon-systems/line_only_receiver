from collections import deque

from twisted.protocols.basic import LineOnlyReceiver
from twisted.protocols.policies import TimeoutMixin
from twisted.internet.defer import fail

from tx_tcp_line_client.utils.command import Command
from tx_tcp_line_client.exceptions import (
    TimeoutError,
    ResponseError,
    ClientError
)


class LineProtocol(LineOnlyReceiver, TimeoutMixin):
    """
    _disconnected: indicate if the connectionLost has been called or not.
    """
    _disconnected = False
    factory = None

    def __init__(self, timeOut=60):
        """
        Create the protocol.

        Parameters:
            timeOut: the timeout to wait before detecting that the connection
        is dead and close it. It's expressed in seconds.

        Instance Parameters:
            _timeOut: Persist the original timeout value
            _queue: A queue of requests waiting for a response from the server
        """
        self._timeOut = self.timeOut = timeOut
        self._queue = deque()

    def _cancelCommands(self, reason):
        """
        Cancel all the outstanding commands, making them fail with C{reason}.
        """
        while self._queue:
            self._queue.popleft().fail(reason)

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
        LineOnlyReceiver.connectionLost(self, reason)

    def lineReceived(self, line):
        """
        Receive line commands from the server.
        """
        self.resetTimeout()

        if line == 'OK':
            self._queue.popleft().success(True)
        else:
            self._queue.popleft().fail(
                ResponseError(
                    "Unknown response received: {0}".format(val)
                )
            )

        if not self._queue:
            # No pending request, remove timeout
            self.setTimeout(None)

    def sendLine(self, line):
        """
        Override sendLine method
        """
        # Set timeout if there isn't already one running
        if not self._queue:
           self.setTimeout(self._timeOut)

        cmdObj = Command('sendLine', line)
        if self._disconnected:
            cmdObj.fail(
                ClientError(
                    "Client has been disconnected and cannot send."
                )
            )

        if not isinstance(line, str):
            cmdObj.fail(
                ClientError(
                    "Invalid type for value: %s, expecting a string" % (type(line),)
                )
            )

        if not cmdObj._deffered.called:
            LineOnlyReceiver.sendLine(self, line)
            self._queue.append(cmdObj)

        return cmdObj._deferred


