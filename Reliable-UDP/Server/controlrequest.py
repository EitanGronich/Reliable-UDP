#!/usr/bin/python

## @package Reliable-UDP.Server.controlrequest
## @file controlrequest.py Implementation of @ref Reliable-UDP.Server.controlrequest

import controlserver
from ..Common import constants
from ..Common import util

## General Control Request
#
# Abstract Control Request, all Control Requests inherit from it.
# Includes simple state logic.
#
class ControlRequest(object):

    ##Name of request (empty because it is an abstract class)
    _NAME = ""

    ##States of a request
    _STATES = (
        _RECEIVE_HEADERS,
        _PREPARE_RESPONSE,
        _SEND_RESPONSE,
        _FINISHED,
    ) = range(4)

    ##Headers the request needs to receive (empty because it is
    # an abstract class)
    _HEADERS_IN = (

    )

    ##Init ControlRequest
    # @param control_socket (ControlSocket) Control Socket
    # @returns (Control Request) Control Request object
    def __init__(self, control_socket):
        ##Current state
        self._state = ControlRequest._RECEIVE_HEADERS
        ##Control socket object
        self._control_socket = control_socket
        ##Receive buffer
        self._buffer = ""
        ##Dictionary of header (in) name to header value
        self._headers_in = {}
        ##Dictionary of header (out) name to header value
        self._headers_out = {}
        ##Boolean - has a response already been sent
        self._sent = False


    ##Parses received buffer.
    # @param buffer (string) buffer.
    def parse_buffer(self, buffer):
        self._buffer += buffer
        while self._FUNCS[self._state](self):
            pass

    ##Receives headers.
    # @returns (bool) finished receiving or not
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

    ##Prepares response
    # @returns (bool) finished preparing or not
    def prepare_response(self):
        self._state = self._SEND_RESPONSE
        return True

    ##Sends response
    # @returns (bool) finished preparing or not
    def send_response(self):
        self._control_socket.send_headers(
            code=constants._CONTROL_OK,
            headers=self._headers_out,
        )
        self._state = self._FINISHED
        self._sent = True
        return True

    ##Nothing. Finished.
    def state_finished(self):
        pass

    ##Immediately close request.
    def close(self):
        self._state = self._FINISHED

    ##Returns whether finished or not.
    # @returns (bool) finished or not
    def finished(self):
        return self._state == self._FINISHED

    ##Map of states to methods
    _FUNCS = {
        _RECEIVE_HEADERS: receive_headers,
        _PREPARE_RESPONSE: prepare_response,
        _SEND_RESPONSE: send_response,
        _FINISHED: state_finished,
    }
