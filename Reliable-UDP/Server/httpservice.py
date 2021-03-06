#!/usr/bin/python

## @package Reliable-UDP.Server.httpservice
## @file httpservice.py Implementation of @ref Reliable-UDP.Server.httpservice

from ..Common import util
from ..Common import constants

## General HTTP Service
#
# Abstract HTTPService, all HTTP Services inherit from it.
# Includes simple state logic.
#
class HTTPService(object):

    ##States of an HTTP Service
    _STATES = (
        _RECEIVE_HEADERS,
        _OPEN,
        _PREPARE_RESPONSE,
        _SEND_HEADERS,
        _SEND_CONTENT,
        _CLOSE,
        _FINISHED,
    ) = range(7)

    ##Headers the service needs to recieve (empty because
    #it is an abstract class)
    _HEADERS_IN = (

    )

    ##Init HTTPService
    # @param http_socket (HTTPSocket) HTTP Socket Object
    # @param parsedurl (urlparse.ParseResult) Parsed request URL
    # @returns (HTTPService) HTTP Service object
    def __init__(self, http_socket, parsedurl):
        ##Current state
        self._state = self._RECEIVE_HEADERS
        ##HTTP socket object
        self._http_socket = http_socket
        ##Receive buffer
        self._buffer = ""
        ##Boolean - has a response been sent or not
        self._sent = False
        ##Parsed url of the request
        self._parsedurl = parsedurl
        self._buffer = ""
        ##Dictionary of header (in) name to header value
        self._headers_in = {}
        ##Dictionary of header (out) name to header value
        self._headers_out = {}
        ##Content of response
        self._content = ""

    ##Parse received buffer
    def parse_buffer(self, buffer):
        self._buffer += buffer
        while self._FUNCS[self._state](self):
            pass

    ##Receive HTTP headers
    # @return (bool) Received or not=(or error)
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

    ##Open file
    # @return (bool) Opened or not
    def open(self):
        self._state = self._PREPARE_RESPONSE
        return True

    ##Prepare response
    # @return (bool) Response prepared or not
    def prepare_response(self):
        self._state = self._SEND_HEADERS
        return True

    ##Send Headers
    # @return (bool) Headers sent or not
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

    ##Send Content
    # @return (bool) Content sent or not
    def send_content(self):
        self._http_socket.queue_buffer(self._content)
        self._state = self._CLOSE
        return True

    ##Close file
    # @return (bool) File closed or not
    def close(self):
        self._state = self._FINISHED
        return True

    ##Nothing. Finished.
    def state_finished(self):
        pass

    ##Return whether service is finished.
    # @return (bool) Finished or not
    def finished(self):
        return self._state == self._FINISHED

    ##Dict of states to mathing methods
    _FUNCS = {
        _RECEIVE_HEADERS: receive_headers,
        _OPEN: open,
        _PREPARE_RESPONSE: prepare_response,
        _SEND_HEADERS: send_headers,
        _SEND_CONTENT: send_content,
        _CLOSE: close,
        _FINISHED: state_finished,
    }
