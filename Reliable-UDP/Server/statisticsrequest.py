#!/usr/bin/python

## @package Reliable-UDP.Server.statisticsrequest
## @file statisticsrequest.py Implementation of @ref Reliable-UDP.Server.statisticsrequest

from controlrequest import ControlRequest
import controlserver
from ..Common import util, constants
from rudpmanager import RUDPManager

## Statistics Request
#
# Inherits from ControlRequest, Represents a request for statistics
# in the control protocol.
#
class StatisticsRequest(ControlRequest):

    ##Name of type of request
    _NAME = "statistics"

    ##Headers this type of request needs to receive
    _HEADERS_IN = (
        "info",
        "rudp_address",
        "rudp_port",
        "cid",
    )

    ##Statistic info types - types of information that can
    #be requested
    _INFO_TYPES = (
        "number_of_connections",
        "bytes_sent",
        "bytes_received",
        "remote_user",
        "connected_user",
        "sequence_number",
        "peer_sequence_number",
    )

    ##Statistic info types that are connection specific
    _CONNECTION_SPECIFIC = (
        "bytes_sent",
        "bytes_received",
        "remote_user",
        "connected_user",
        "sequence_number",
        "peer_sequence_number",
    )

    ##Statistic info types that are not connection-specific
    _GENERAL = (
        "number_of_connections"
    )

    ##Init StatisticsRequest
    # @param control_socket (ControlSocket) Control Socket
    # @returns (StatisticsRequest) StatisticsRequest object
    def __init__(self, control_socket):
        super(StatisticsRequest, self).__init__(
            control_socket
        )

    ##Prepare request response.
    ## @returns (bool) Preparation has been finished or not
    def prepare_response(self):
        self.check_headers()
        info = self._headers_in["info"]
        if info == "number_of_connections":
            self._headers_out["number_of_connections"] = len(self._control_socket._rudp_manager._connections)
        else:
            exit_addr = self._headers_in["rudp_address"], self._headers_in["rudp_port"]
            cid = self._headers_in["cid"]
            if info == "bytes_sent":
                self._headers_out["bytes_sent"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._bytes_sent
            elif info == "bytes_received":
                self._headers_out["bytes_received"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._bytes_received
            elif info == "remote_user":
                self._headers_out["remote_user"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._remote_user
            elif info == "connected_user":
                self._headers_out["connected_user"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._close_user
            elif info == "sequence_number":
                self._headers_out["sequence_number"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._sequence_num
            elif info == "peer_sequence_number":
                self._headers_out["peer_sequence_number"] = self._control_socket._rudp_manager._connections_by_rudp_server[exit_addr][cid]._peer_sequence_num
        return super(StatisticsRequest, self).prepare_response()

    ##Check received headers. Raise error if invalid.
    def check_headers(self):
        if self._headers_in["info"] not in self._INFO_TYPES:
            raise controlserver.ControlError(code=constants._CONTROL_INVALID_REQUEST, message="Invalid Request")

        if self._headers_in["info"] in self._CONNECTION_SPECIFIC:
            if not all(
                (
                    self._headers_in["rudp_address"],
                    self._headers_in["rudp_port"],
                    self._headers_in["cid"],
                )
            ):
                raise controlserver.ControlError(code=constants._CONTROL_INVALID_REQUEST, message="Invalid Request")

            cid = self._headers_in["cid"] = util.str_to_int(self._headers_in["cid"])
            rudp_port = self._headers_in["rudp_port"] = util.str_to_int(self._headers_in["rudp_port"])
            addr = self._headers_in["rudp_address"], rudp_port
            if any(
                [
                    a is None for a in (
                        cid,
                        rudp_port,
                        util.check_tcp_address(addr),
                    )
                ]
            ):
                raise controlserver.ControlError(code=constants._CONTROL_INVALID_REQUEST, message="Invalid Request")

            if addr not in self._control_socket._rudp_manager._connections_by_rudp_server:
                raise controlserver.ControlError(code=constants._CONTROL_CONNECTION_NOT_EXIST, message="Connection Does Not Exist")

            if cid not in self._control_socket._rudp_manager._connections_by_rudp_server[addr]:
                raise controlserver.ControlError(code=constants._CONTROL_CONNECTION_NOT_EXIST, message="Connection Does Not Exist")

    ##Dict of state to matching method
    _FUNCS = {
        ControlRequest._RECEIVE_HEADERS: ControlRequest.receive_headers,
        ControlRequest._PREPARE_RESPONSE: prepare_response,
        ControlRequest._SEND_RESPONSE: ControlRequest.send_response,
        ControlRequest._FINISHED: ControlRequest.state_finished,
    }
