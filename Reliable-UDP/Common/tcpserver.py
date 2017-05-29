#!/usr/bin/python

## @package Reliable-UDP.Common.tcpserver
## @file tcpserver.py Implementation of @ref Reliable-UDP.Common.tcpserver

from asyncio import BaseEvent
import errno
import socket
import traceback
from asyncsocket import AsyncSocket
import logging

## DisconnectError
#
# Inherits from RuntimeError, indicates disconnection in TCP.
#
class DisconnectError(RuntimeError):

    ##Init DisconnectError
    # @param msg (string) message
    # @returns (DisconnectError) DisconnectError object
    def __init__(self, msg):
        super(DisconnectError, self).__init__(msg)

## General Non-Listener Socket
#
# Inherits from AsyncSocket, has mechanisms for connect, send buffer,
# receive buffer, disconnect etc.
#
class TCPServerSocket(AsyncSocket):

    """
        Generic class of TCP sockets that are not listeners.
        These are pollable objects and in addition
        include maximum block size and buff limits,
        send and receive buffers, and a boolean regarding
        whether they are open to receive or not.
    """
    ##Stages of an async connection to a TCP destination
    _CONNECT_STATES = (
        _BEFORE_CONNECT,
        _CONNECTING,
        _CONNECTED,
    ) = range(3)

    ##Inits TCPServerSocket
    # @param async_manager (Poller) Poller object
    # @param timeout (int) default timeout in milliseconds
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @param s (socket) socket
    # @param connect_address (tuple) connect address
    # @returns TCPServerSocket object
    def __init__(
        self,
        async_manager,
        timeout,
        block_size,
        buff_limit,
        s=None,
        connect_address=None,
    ):
        if s:
            ##Stage of connection
            self._state = self._CONNECTED
        else:
            assert connect_address is not None
            ##Address to connect to
            self._connect_address = connect_address
            self._state = self._BEFORE_CONNECT
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
            )
            s.setblocking(0)
        super(TCPServerSocket, self).__init__(
            async_manager=async_manager,
            socket=s,
            timeout=timeout,
        )
        ##Send buffer
        self._send_buff = ""
        ##Receive buffer
        self._recv_buff = ""
        ##Read block size
        self._block_size = block_size
        ##Receive buff limit
        self._buff_limit = buff_limit

    ##Updates TCPServerSocket
    def update(self):
        if self._closing and not self._send_buff:
            self.terminate()

    ##Logic on read event
    def read(self):
        try:
            while True:
                if not self.receiving():
                    break
                buf = self._s.recv(self._block_size)
                if not buf:
                    raise IOError('Disconnect')
                self.log_data_received(buf)
                self.handle_buf_received(buf)
        except IOError as e:
            if e.errno == errno.ECONNRESET or str(e) == 'Disconnect':
                self.user_disconnected()
            elif e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise

    ##Logic on write event
    def write(self):
        try:
            if self._state == self._BEFORE_CONNECT:
                self._state = self._CONNECTING
                try:
                    self._s.connect(self._connect_address)
                except IOError as e:
                    if e.errno != errno.EINPROGRESS:
                        raise e
            elif self._state == self._CONNECTING:
                self._state = self._CONNECTED
                self.approve_connection()
            elif self._state == self._CONNECTED:
                while self._send_buff:
                    n = self._s.send(self._send_buff)
                    buf_sent = self._send_buff[:n]
                    self._send_buff = self._send_buff[n:]
                    self.handle_buf_sent(buf_sent)
                    self.log_data_sent(buf_sent)
        except IOError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise

    ##Logic on TCP buffer received
    # @param buf (string) buffer
    def handle_buf_received(self, buf):
        pass

    ##Logic on TCP buffer sent
    # @param buf (string) buffer
    def handle_buf_sent(self, buf):
        pass

    ##Log when data is sent
    # @param buf_sent (string) buffer sent
    def log_data_sent(self, buf_sent):
        logging.info(
            (
                "%s: Data sent: Address: %s; Data: %s"
            ) % (
                self,
                self._s.getpeername(),
                buf_sent,
            )
        )

    ##Log when data is received
    # @param buf (string) buffer received
    def log_data_received(self, buf):
        logging.info(
            (
                "%s: Data received from: Address: %s; Data: %s"
            ) % (
                self,
                self._s.getpeername(),
                buf,
            )
        )

    ##Returns IO mask for TCPServerSocket
    # @returns (int) IO mask
    def get_io_mask(self):
        mask = BaseEvent.POLLERR
        if self._send_buff or (not self._closing and self._state in (self._BEFORE_CONNECT, self._CONNECTING)):
            mask |= BaseEvent.POLLOUT
        if not self._closing and self.receiving():
            mask |= BaseEvent.POLLIN
        return mask

    ##Queues TCP buffer to be sent
    # @param buffer (string) buffer to be sent
    def queue_buffer(self, buffer):
        self._send_buff += buffer

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "TCP Socket (%s)" % self._fileno

    ##Returns whether TCPServerSocket is receiving
    # @returns (bool) receiving or not
    def receiving(self):
        return len(self._recv_buff) <= self._buff_limit

    ##Logic on connection success
    def approve_connection(self):
        pass

    ##Logic on user disconnect
    def user_disconnected(self):
        logging.info(
            "%s: User at %s disconnected" % (self, self._s.getpeername())
        )
        raise DisconnectError('Disconnected')


## General Listener Socket
#
# Inherits from AsyncSocket, only listens for connections and makes
# TCP sockets.
#
class TCPServerListener(AsyncSocket):

    """
        Generic class of TCP listener sockets.
        These are pollable objects and in addition
        include maximum block size and buff limits.
        Since listener sockets do not actually receive
        buffers, these attributes are only passed on
        to created TCP sockets.
    """

    ##Inits TCPListenerSocket
    # @param bind_address (tuple) bind address
    # @param async_manager (Poller) Poller object
    # @param timeout (int) default timeout in milliseconds
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @returns TCPServerListener object
    def __init__(
        self,
        bind_address,
        async_manager,
        timeout,
        block_size,
        buff_limit,
    ):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        s.setblocking(0)
        s.bind(bind_address)
        s.listen(10)
        super(TCPServerListener, self).__init__(
            async_manager=async_manager,
            socket=s,
            timeout=timeout,
        )
        ##Read block size to pass on to created sockets
        self._block_size = block_size
        ##Receive buff limit to pass on to created sockets
        self._buff_limit = buff_limit

    ##Logic on read event
    def read(self):
        s1 = None
        try:
            s1, addr = self._s.accept()
            logging.info(
                "%s: Connection accepted from %s" % (self, s1.getpeername())
            )
            s1.setblocking(0)
            TCPServerSocket(
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

    ##Return IO mask for the object.
    # @returns (int) IO mask
    def get_io_mask(self):
        mask = BaseEvent.POLLERR
        if not self._closing:
            mask |= BaseEvent.POLLIN
        return mask

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "TCP Listener Socket (s)" % self._fileno
