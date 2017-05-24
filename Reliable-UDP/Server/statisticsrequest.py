from controlrequest import ControlRequest
import controlserver
from ..Common import util, constants

class StatisticsRequest(ControlRequest):

    _NAME = "statistics"

    _HEADERS_IN = (
        "info",
        "rudp_address",
        "rudp_port",
        "cid",
    )

    _INFO_TYPES = (
        "number_of_connections",
        "bytes_sent",
        "bytes_received",
    )

    _CONNECTION_SPECIFIC = (
        "bytes_sent",
        "bytes_received",
    )

    _GENERAL = (
        "number_of_connections"
    )

    def __init__(self, control_socket):
        super(StatisticsRequest, self).__init__(
            control_socket
        )

    def prepare_response(self):
        self.check_headers()
        if self._headers_in["info"] == "number_of_connections":
            self._headers_out["number_of_connections"] = len(self._control_socket._rudp_manager._connections)
        elif self._headers_in["info"] == "bytes_sent":
            self._headers_out["bytes_sent"] = self._control_socket._rudp_manager._connections_by_rudp_server[
                (self._headers_in["rudp_address"], self._headers_in["rudp_port"])
            ][self._headers_in["cid"]]._bytes_sent
        return super(StatisticsRequest, self).prepare_response()

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

    _FUNCS = {
        ControlRequest._RECEIVE_HEADERS: ControlRequest.receive_headers,
        ControlRequest._PREPARE_RESPONSE: prepare_response,
        ControlRequest._SEND_RESPONSE: ControlRequest.send_response,
        ControlRequest._FINISHED: ControlRequest.state_finished,
    }
