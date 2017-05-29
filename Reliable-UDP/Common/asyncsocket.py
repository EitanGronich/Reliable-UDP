#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Common.asyncsocket
## @file asyncsocket.py Implementation of @ref Reliable-UDP.Reliable-UDP.Common.asyncsocket

from pollableobject import PollableObject
import socket
import logging

## General socket object
#
# Surrounds PollableObject only with socket close at terminate and
# error discovery when POLLERR is received, using getsockopt().
#
class AsyncSocket(PollableObject):

    ##Init function for AsyncSocket
    # @param async_manager (Poller) Poller object
    # @param socket (socket) socket object
    # @param timeout (int) default timeout in milliseconds
    # @returns (AsyncSocket) AsyncSocket object
    def __init__(
        self,
        async_manager,
        socket,
        timeout,
    ):
        ##TCP Socket
        self._s = socket
        super(AsyncSocket, self).__init__(
            async_manager=async_manager,
            fileno=socket.fileno(),
            timeout=timeout,
        )

    ##Terminate AsyncSocket object.
    def terminate(self):
        self._s.close()
        super(AsyncSocket, self).terminate()

    ##logs a Pollerr object
    def log_error(self):
        logging.error(
            "%s: Pollerr received:\n"
            "%s" % (
                self,
                self._s.getsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_ERROR,
                )
            )
        )
