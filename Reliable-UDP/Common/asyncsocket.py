#!/usr/bin/python

from pollableobject import PollableObject
import socket
import logging

class AsyncSocket(PollableObject):

    def __init__(
        self,
        async_manager,
        socket,
        timeout,
    ):
        self._s = socket
        super(AsyncSocket, self).__init__(
            async_manager=async_manager,
            fileno=socket.fileno(),
            timeout=timeout,
        )

    def terminate(self):
        self._s.close()
        super(AsyncSocket, self).terminate()

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
