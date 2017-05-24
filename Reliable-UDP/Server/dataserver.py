#!/usr/bin/python

import traceback
from ..Common import constants
from ..Common.tcpserver import TCPServerSocket, TCPServerListener
from datetime import datetime, timedelta
import rudpconnection
import logging

class DataSocket(TCPServerSocket):

    """
        Class of sockets that handle actual data
        transmitted via the connection.
    """

    def __init__(
        self,
        async_manager,
        rudp_manager,
        timeout,
        block_size,
        buff_limit,
        socket=None,
        connect_address=None,
        exit_address=None,
        dest_address=None,
        connection=None,
    ):
        super(DataSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
            s=socket,
            connect_address=connect_address,
        )
        self._rudp_manager = rudp_manager
        if exit_address is not None and dest_address is not None and socket is not None:
            self._exit_address = exit_address
            self._dest_address = dest_address
            self._connection = self._rudp_manager.init_connection(
                rudp_exit=exit_address,
                initiator=self._s.getpeername(),
                endpoint=dest_address,
                data_socket=self,
            )
        else:
            assert connect_address is not None and connection is not None
            self._connection = connection

    def handle_buf_received(self, buf):
        self._recv_buff += buf
        if self._connection._connection_state not in (
            rudpconnection.RUDPConnection._WAITING_FOR_ACK,
            rudpconnection.RUDPConnection._WAITING_FOR_INIT_ACK,
            rudpconnection.RUDPConnection._WAITING_CONNECTION_APPROVAL,
        ):
            self._connection.queue_buffer(self._recv_buff)
            self._recv_buff = ""

    def approve_connection(self):
        self._connection.approve_data_socket()

    def __repr__(self):
        return "Data Socket (%s)" % self._fileno

    def receiving(self):
        return (
            len(self._recv_buff) < self._buff_limit
            and self._connection
            and self._connection._connection_state not in (
                rudpconnection.RUDPConnection._WAITING_FOR_ACK,
                rudpconnection.RUDPConnection._WAITING_FOR_INIT_ACK,
                rudpconnection.RUDPConnection._WAITING_CONNECTION_APPROVAL,
            )
        )


    def terminate(self):
        super(DataSocket, self).terminate()
        self.close_connection()

    def close_connection(self):
        if self._connection and not self._connection._closing:
            self._connection.init_close()
        self._connection = None



class DataListener(TCPServerListener):

    """
        Class of listener sockets that accept data connections.
    """

    def __init__(
        self,
        bind_address,
        exit_address,
        dest_address,
        async_manager,
        rudp_manager,
        timeout,
        block_size,
        buff_limit,
        ttl,
    ):
        super(DataListener, self).__init__(
            bind_address=bind_address,
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
        )
        self._rudp_manager = rudp_manager
        self._exit_address = exit_address
        self._dest_address = dest_address
        self._accepted = False
        self._ttl = ttl
        self._time_to_close = datetime.now() + timedelta(seconds=ttl)

    def update(self):
        if self._ttl and datetime.now() >= self._time_to_close:
            self.init_close()
        return super(DataListener, self).update()

    def read(self):
        s1 = None
        try:
            s1, addr = self._s.accept()
            logging.info(
                "%s: Data Connection accepted from %s" % (self, s1.getpeername())
            )
            s1.setblocking(0)
            DataSocket(
                async_manager=self._async_manager,
                rudp_manager=self._rudp_manager,
                exit_address=self._exit_address,
                dest_address=self._dest_address,
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

    def get_sleep_time(self):
        t = constants._TIMEOUT
        if self._ttl and not self._closing:
            t = min (
                t, (self._time_to_close - datetime.now()).total_seconds() * 1000.0,
            )
        return t


    def __repr__(self):
        return "Data Listener Socket (%s)" % self._fileno
