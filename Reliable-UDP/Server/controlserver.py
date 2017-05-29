#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Server.controlserver
## @file controlserver.py Implementation of @ref Reliable-UDP.Reliable-UDP.Server.controlserver


import traceback
from ..Common.tcpserver import TCPServerSocket, TCPServerListener
from connectrequest import ConnectRequest
from statisticsrequest import StatisticsRequest
from ..Common import constants
import logging

## Control Protocol Error
#
# Used to alert when there is a problem with a control request.
# Error code is sent to user.
#
class ControlError(RuntimeError):

    ##Init Control Error
    # @param (int) error code
    # @param (string) error message
   def __init__(self, code, message):
       super(ControlError, self).__init__(message)
       ##Message of error
       self.message = message
       ##Code of error
       self.code = code

    ##Returns error code
    # @returns (int) code
   def code(self):
       return self.code

    ##Returns error message
    # @returns (string) message
   def message(self):
       return self.message

## Control Socket
#
# Inherits from TCPServerSocket, deals with data sent and received from users in the
# control protocol.
#
class ControlSocket(TCPServerSocket):

    """
        Class of sockets that handle control
        connection with users. This kind of connection
        facilitates the user asking for connections and also
        for statistics.
    """

    ##Dictionary of request type names to request type classes
    _REQUEST_CLASSES = {
        "connect": ConnectRequest,
        "statistics": StatisticsRequest,
    }

    ##Inits ControlSocket
    # @param async_manager (Poller) Poller object
    # @param rudp_manager (RUDPManager) RUDP Manager object
    # @param timeout (int) default timeout in milliseconds
    # @param socket (socket) socket
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @returns (ControlSocket) object
    def __init__(
            self,
            async_manager,
            rudp_manager,
            timeout,
            socket,
            block_size,
            buff_limit,
        ):
        super(ControlSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            s=socket,
            block_size=block_size,
            buff_limit=buff_limit,
        )
        ##Current request in process
        self._current_request = None
        ##RUDP manager object
        self._rudp_manager = rudp_manager

    ##Handles buffer received.
    # @param buf (string) buffer
    def handle_buf_received(self, buf):
        self._recv_buff += buf
        self.parse_buffer()

    ##Parses current buffer
    def parse_buffer(self):
        if self._current_request:
            try:
                self._current_request.parse_buffer(self._recv_buff)
            except Exception as e:
                logging.info(
                    "%s: %s" % (self, traceback.format_exc())
                )
                if not self._current_request._sent:
                    self.send_error(e)
                self._current_request.close()

            if self._current_request.finished():
                self._current_request = None
                self._recv_buff = ""
        else:
            try:
                op = self.parse_op()
                if op is not None:
                    self._current_request = op(self)
                    self.parse_buffer()
            except Exception as e:
                logging.info(
                    "%s: %s" % (self, traceback.format_exc())
                )
                self.send_error(e)
                self._current_request = None
                self._recv_buff = ""

    ##Parses operation (op) - statistics or connect.
    # @returns (ControlRequest) type of request
    def parse_op(self):
        i = self._recv_buff.find("\n")
        if i != -1:
            line, buf = self._recv_buff[:i], self._recv_buff[(i+1):]
            i = line.find("=")
            if i == -1:
                raise ControlError(code=1, message="Invalid Header")
            field, op = line.split("=")
            if field != "op" or op not in ControlSocket._REQUEST_CLASSES:
                raise ControlError(code=1, message="Invalid Header")
            self._recv_buff = buf
            return ControlSocket._REQUEST_CLASSES[op]

    ##Sends error code to user
    # @param e (Exception) error
    def send_error(self, e):
        if type(e).__name__ == "ControlError":
            code = e.code
        else:
            code = constants._CONTROL_INVALID_REQUEST
        self.send_headers(
            code=code,
            headers={},
        )

    ##Sends response headers to user.
    # @param code (int) code
    # @param headers (dict) headers
    def send_headers(self, code, headers):
        if self._current_request:
            self.queue_buffer(
                "op=%s\n" % self._current_request._NAME
            )
        self.queue_buffer(
            "code=%s\n" % code
        )
        for k, v in headers.items():
            self.queue_buffer(
                "%s=%s\n" % (k,v)
            )
        self.queue_buffer("\n")

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Control Socket (%s)" % self._fileno


## Control Listener Socket
#
# Inherits from TCPServerListener, only listens for connections and makes
# Control sockets.
#
class ControlListener(TCPServerListener):

    """
        Class of listener sockets that accept
        control connections, through which users ask for connections and also
        for statistics.
    """

    ##Inits ControlListener
    # @param bind_address (tuple) bind address
    # @param async_manager (Poller) Poller object
    # @param rudp_manager (RUDPManager) RUDPManager object
    # @param timeout (int) default timeout in milliseconds
    # @param block_size (int) reading block size in bytes
    # @param buff_limit (int) receiving buff limit in bytes
    # @returns (ControlListener) object
    def __init__(
        self,
        bind_address,
        async_manager,
        rudp_manager,
        timeout,
        block_size,
        buff_limit,
    ):
        super(ControlListener, self).__init__(
            bind_address=bind_address,
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
        )
        ##RUDP Manager object
        self._rudp_manager = rudp_manager

    ##Logic on read event. Accepts connections.
    def read(self):
        s1 = None
        try:
            s1, addr = self._s.accept()
            logging.info(
                "%s: Control Connection accepted from %s" % (self, s1.getpeername())
            )
            s1.setblocking(0)
            ControlSocket(
                async_manager=self._async_manager,
                rudp_manager=self._rudp_manager,
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
        return "Control Listener Socket (%s)" % self._fileno
