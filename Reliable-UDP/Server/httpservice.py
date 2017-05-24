#!/usr/bin/python

from ..Common import util
from ..Common import constants

class HTTPService(object):

    _STATES = (
        _RECEIVE_HEADERS,
        _OPEN,
        _PREPARE_RESPONSE,
        _SEND_HEADERS,
        _SEND_CONTENT,
        _CLOSE,
        _FINISHED,
    ) = range(7)

    _HEADERS_IN = (

    )

    def __init__(self, http_socket, parsedurl):
        self._state = self._RECEIVE_HEADERS
        self._http_socket = http_socket
        self._buffer = ""
        self._sent = False
        self._fd = None
        self._parsedurl = parsedurl
        self._headers_in = {}
        self._headers_out = {}
        self._content = ""

    def parse_buffer(self, buffer):
        self._buffer += buffer
        while self._FUNCS[self._state](self):
            pass

    def receive_headers(self):
        n = self._buffer.find("%s%s" %(constants._CRLF_BIN, constants._CRLF_BIN))
        if n == - 1:
            return
        self._headers_in = {v: '' for v in self._HEADERS_IN}
        SEP = ':'
        for i in range(constants._MAX_NUMBER_OF_HEADERS):
            line, self._buffer = util.split_buffer(self._buffer, constants._CRLF_BIN)
            if not line:
                break
            n = line.find(SEP)
            if n == -1:
                raise RuntimeError('Invalid header received')
            header_name, value = line[:n].rstrip(), line[n + len(SEP):].lstrip()
            if header_name in self._HEADERS_IN:
                self._headers_in[header_name] = value

        else:
            raise RuntimeError('Too many headers')
        self._state = self._OPEN
        return True

    def open(self):
        self._state = self._PREPARE_RESPONSE
        return True

    def prepare_response(self):
        self._state = self._SEND_HEADERS
        return True

    def send_headers(self):
        self._http_socket.send_headers(
            code=constants._HTTP_OK_CODE,
            message=constants._HTTP_OK_MESSAGE,
            content_length=self._content_length,
            content_type=self._content_type,
            headers=self._headers_out,
        )
        self._state = self._SEND_CONTENT
        self._sent = True
        return True

    def send_content(self):
        self._http_socket.queue_buffer(self._content)
        self._state = self._CLOSE
        return True

    def close(self):
        self._state = self._FINISHED
        return True

    def state_finished(self):
        pass

    def finished(self):
        return self._state == self._FINISHED

    _FUNCS = {
        _RECEIVE_HEADERS: receive_headers,
        _OPEN: open,
        _PREPARE_RESPONSE: prepare_response,
        _SEND_HEADERS: send_headers,
        _SEND_CONTENT: send_content,
        _CLOSE: close,
        _FINISHED: state_finished,
    }
