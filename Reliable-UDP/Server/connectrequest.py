from controlrequest import ControlRequest
import controlserver
from dataserver import DataListener
from ..Common import util, constants

class ConnectRequest(ControlRequest):

    _NAME = "connect"

    _HEADERS_IN = (
        "exit_address",
        "exit_port",
        "dest_address",
        "dest_port",
        "ttl",
    )

    def __init__(self, control_socket):
        super(ConnectRequest, self).__init__(
            control_socket
        )

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

    _FUNCS = {
        ControlRequest._RECEIVE_HEADERS: ControlRequest.receive_headers,
        ControlRequest._PREPARE_RESPONSE: prepare_response,
        ControlRequest._SEND_RESPONSE: ControlRequest.send_response,
        ControlRequest._FINISHED: ControlRequest.state_finished,
    }
