#!/usr/bin/python

## @package Reliable-UDP.Test_Async.Echoer.echoserver
## @file echoserver.py Implementation of @ref  Reliable-UDP.Test_Async.Echoer.echoserver

import traceback
from ...Common.tcpserver import TCPServerSocket, TCPServerListener
import logging

## Echo Socket
#
# Inherits from TCPServerSocket, simply echos all data
# received.
#
class EchoSocket(TCPServerSocket):

    """
        Class of sockets that echo everything received.
    """
    ##Inits EchoSocket
    # @param async_manager (Poller) Poller object
    # @param timeout (int) default timeout in milliseconds
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @param socket (socket) socket
    # @param connect_address (tuple) Address to connect to, always None
    # for this object
    # @returns (EchoSocket) object
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

    ##Handle buffer received - immediately transmit back.
    def handle_buf_received(self, buf):
        self.queue_buffer(buf)

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Echo Socket (%s)" % self._fileno

## Echo Listener Socket
#
# Inherits from TCPServerListener, only listens for connections and makes
# Echo sockets.
#
class EchoListener(TCPServerListener):

    """
        Class of listener sockets that accept echo connections.
    """
    ##Inits EchoListener
    # @param bind_address (tuple) bind address
    # @param async_manager (Poller) Poller object
    # @param timeout (int) default timeout in milliseconds
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @returns (EchoListener) object
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

    ##Receive read event - accept connections and make EchoSocket.
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

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Echo Listener Socket (%s)" % self._fileno
