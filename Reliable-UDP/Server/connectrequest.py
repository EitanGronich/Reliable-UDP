#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Server.connectrequest
## @file connectrequest.py Implementation of @ref Reliable-UDP.Reliable-UDP.Server.connectrequest

from controlrequest import ControlRequest
import controlserver
from dataserver import DataListener
from ..Common import util, constants

## Connect (Listener Port) Request
#
# Control request that asks to open a listening port.
#
class ConnectRequest(ControlRequest):

    #Name of request
    _NAME = "connect"

    #Headers the request needs to receive
    _HEADERS_IN = (
        "exit_address",
        "exit_port",
        "dest_address",
        "dest_port",
        "ttl",
    )

    ##Init Connect Request
    # @param control_socket (ControlSocket) Control Socket
    # @returns (ConnectRequest) Connect Request object
    def __init__(self, control_socket):
        super(ConnectRequest, self).__init__(
            control_socket
        )

    ##Prepares response for send.
    # @returns (bool) finished preparing or not
    def prepare_response(self):
        self.check_headers()
        dl = DataListener(
            async_manager=self._control_socket._async_manager,
            bind_address=("0.0.0.0", 0),
            exit_address=(self._headers_in["exit_address"], self._headers_in["exit_port"]),
            dest_address=(self._headers_in["dest_address"], self._headers_in["dest_port"]),
            rudp_manager=self._control_socket._rudp_manager,
            timeout=self._control_socket._timeout,
            block_size=constants._DATA_BLOCK_SIZE,
            buff_limit=constants._DATA_BUFF_LIMIT,
            ttl=self._headers_in["ttl"],
        )
        self._headers_out["port"] = dl._s.getsockname()[1]
        return super(ConnectRequest, self).prepare_response()

    ##Check if headers are proper. If not raise error.
    def check_headers(self):
        ttl = self._headers_in["ttl"] = util.str_to_float(self._headers_in["ttl"])
        exit_port = self._headers_in["exit_port"] = util.str_to_int(self._headers_in["exit_port"])
        dest_port = self._headers_in["dest_port"] = util.str_to_int(self._headers_in["dest_port"])
        if any(
            [
                a is None for a in (
                    ttl,
                    exit_port,
                    dest_port,
                    util.check_tcp_address(
                        (self._headers_in["exit_address"], exit_port)
                    ),
                    util.check_tcp_port(
                        dest_port
                    ),
                )
            ]
        ):
            raise controlserver.ControlError(code=constants._CONTROL_INVALID_REQUEST, message="Invalid Request")

    ##Map of states to methods
    _FUNCS = {
        ControlRequest._RECEIVE_HEADERS: ControlRequest.receive_headers,
        ControlRequest._PREPARE_RESPONSE: prepare_response,
        ControlRequest._SEND_RESPONSE: ControlRequest.send_response,
        ControlRequest._FINISHED: ControlRequest.state_finished,
    }
