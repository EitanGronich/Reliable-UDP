#!/usr/bin/python

import controlserver
from ..Common import constants
from ..Common import util

class ControlRequest(object):

    _NAME = ""

    _STATES = (
        _RECEIVE_HEADERS,
        _PREPARE_RESPONSE,
        _SEND_RESPONSE,
        _FINISHED,
    ) = range(4)

    _HEADERS_IN = (

    )

    def __init__(self, control_socket):
        self._state = ControlRequest._RECEIVE_HEADERS
        self._control_socket = control_socket
        self._buffer = ""
        self._headers_in = {}
        self._headers_out = {}
        self._sent = False


    def parse_buffer(self, buffer):
        self._buffer += buffer
        while self._FUNCS[self._state](self):
            pass

    def receive_headers(self):
        n = self._buffer.find("%s%s" %(constants._LF_BIN, constants._LF_BIN))
        if n == - 1:
            return
        self._headers_in = {v: '' for v in self._HEADERS_IN}
        SEP = '='
        for i in range(constants._MAX_NUMBER_OF_HEADERS):
            line, self._buffer = util.split_buffer(self._buffer, constants._LF_BIN)
            if not line:
                break
            n = line.find(SEP)
            if n == -1:
                raise controlserver.ControlError(code=1, message="Invalid Header")
            header_name, value = line[:n].rstrip(), line[n + len(SEP):].lstrip()
            if header_name in self._HEADERS_IN:
                self._headers_in[header_name] = value

        else:
            raise controlserver.ControlError(code=1, message="Too Many Headers")
        self._state = self._PREPARE_RESPONSE
        return True

    def prepare_response(self):
        self._state = self._SEND_RESPONSE
        return True

    def send_response(self):
        self._control_socket.send_headers(
            code=constants._CONTROL_OK,
            headers=self._headers_out,
        )
        self._state = self._FINISHED
        self._sent = True
        return True

    def state_finished(self):
        pass

    def close(self):
        self._state = self._FINISHED

    def finished(self):
        return self._state == self._FINISHED

    _FUNCS = {
        _RECEIVE_HEADERS: receive_headers,
        _PREPARE_RESPONSE: prepare_response,
        _SEND_RESPONSE: send_response,
        _FINISHED: state_finished,
    }
