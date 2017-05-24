#!/usr/bin/python

import traceback
from ..Common.tcpserver import TCPServerSocket, TCPServerListener
from connectrequest import ConnectRequest
from statisticsrequest import StatisticsRequest
from ..Common import constants
import logging

class ControlError(RuntimeError):
   def __init__(self, code, message):
       super(ControlError, self).__init__(message)
       self.message = message
       self.code = code

   def code(self):
       return self.code

   def message(self):
       return self.message

class ControlSocket(TCPServerSocket):

    """
        Class of sockets that handle control
        connection with users. This kind of connection
        facilitates the user asking for connections and also
        for statistics.
    """

    _REQUEST_CLASSES = {
        "connect": ConnectRequest,
        "statistics": StatisticsRequest,
    }

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
        self._current_request = None
        self._rudp_manager = rudp_manager

    def handle_buf_received(self, buf):
        self._recv_buff += buf
        self.parse_buffer()

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

    def send_error(self, e):
        if type(e).__name__ == "ControlError":
            code = e.code
        else:
            code = constants._CONTROL_INVALID_REQUEST
        self.send_headers(
            code=code,
            headers={},
        )

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


    def __repr__(self):
        return "Control Socket (%s)" % self._fileno



class ControlListener(TCPServerListener):

    """
        Class of listener sockets that accept
        control connections, through which users ask for connections and also
        for statistics.
    """

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
        self._rudp_manager = rudp_manager

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

    def __repr__(self):
        return "Control Listener Socket (%s)" % self._fileno
