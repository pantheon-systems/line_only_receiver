# pylint: disable=unused-import
from twisted.internet.defer import TimeoutError


class ClientError(Exception):
    """
    Error caused by an invalid client call.
    """


class ResponseError(Exception):
    """
    Error caused by a bad response
    """


class ServerError(Exception):
    """
    Problem happening on the server.
    """

