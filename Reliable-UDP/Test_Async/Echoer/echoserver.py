#!/usr/bin/python

import traceback
import logging
from ...Common.tcpserver import TCPServerSocket, TCPServerListener

class EchoSocket(TCPServerSocket):

    """
        Class of sockets that echo everything received.
    """

    def __init__(
        self,
        async_manager,
        timeout,
        block_size,
        buff_limit,
        socket=None,
        connect_address=None,
    ):
        super(EchoSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
            s=socket,
            connect_address=connect_address,
        )

    def handle_buf_received(self, buf):
        self.queue_buffer(buf)

    def __repr__(self):
        return "Echo Socket (%s)" % self._fileno

class EchoListener(TCPServerListener):

    """
        Class of listener sockets that accept echo connections.
    """

    def __init__(
        self,
        bind_address,
        async_manager,
        timeout,
        block_size,
        buff_limit,
    ):
        super(EchoListener, self).__init__(
            bind_address=bind_address,
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
        )


    def read(self):
        s1 = None
        try:
            s1, addr = self._s.accept()
            self._accepted = True
            logging.info(
                "%s: Connection accepted from %s" % (self, s1.getpeername())
            )
            s1.setblocking(0)
            EchoSocket(
                async_manager=self._async_manager,
                timeout=self._timeout,
                socket=s1,
                block_size=self._block_size,
                buff_limit=self._buff_limit,
            )
        except IOError:
            logging.error(
                "%s: Failed to initalize connection:\n%s" % (self, traceback.format_exc())
            )
            if s1:
                s1.close()

    def __repr__(self):
        return "Echo Listener Socket (%s)" % self._fileno
