#!/usr/bin/python

from asyncio import BaseEvent
import errno
import socket
import traceback
from asyncsocket import AsyncSocket
import logging

class DisconnectError(RuntimeError):

    def __init__(self, msg):
        super(DisconnectError, self).__init__(msg)

class TCPServerSocket(AsyncSocket):

    """
        Generic class of TCP sockets that are not listeners.
        These are pollable objects and in addition
        include maximum block size and buff limits,
        send and receive buffers, and a boolean regarding
        whether they are open to receive or not.
    """

    _CONNECT_STATES = (
        _BEFORE_CONNECT,
        _CONNECTING,
        _CONNECTED,
    ) = range(3)

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
            self._state = self._CONNECTED
        else:
            assert connect_address is not None
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
        self._send_buff = ""
        self._recv_buff = ""
        self._block_size = block_size
        self._buff_limit = buff_limit

    def update(self):
        if self._closing and not self._send_buff:
            self.terminate()

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

    def handle_buf_received(self, buf):
        pass

    def handle_buf_sent(self, buf):
        pass

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

    def get_io_mask(self):
        mask = BaseEvent.POLLERR
        if self._send_buff or (not self._closing and self._state in (self._BEFORE_CONNECT, self._CONNECTING)):
            mask |= BaseEvent.POLLOUT
        if not self._closing and self.receiving():
            mask |= BaseEvent.POLLIN
        return mask

    def queue_buffer(self, buffer):
        self._send_buff += buffer

    def __repr__(self):
        return "TCP Socket (%s)" % self._fileno

    def receiving(self):
        return len(self._recv_buff) <= self._buff_limit

    def approve_connection(self):
        pass

    def user_disconnected(self):
        logging.info(
            "%s: User at %s disconnected" % (self, self._s.getpeername())
        )
        raise DisconnectError('Disconnected')



class TCPServerListener(AsyncSocket):

    """
        Generic class of TCP listener sockets.
        These are pollable objects and in addition
        include maximum block size and buff limits.
        Since listener sockets do not actually receive
        buffers, these attributes are only passed on
        to created TCP sockets.
    """

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
        self._block_size = block_size
        self._buff_limit = buff_limit

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

    def get_io_mask(self):
        mask = BaseEvent.POLLERR
        if not self._closing:
            mask |= BaseEvent.POLLIN
        return mask

    def __repr__(self):
        return "TCP Listener Socket (s)" % self._fileno
