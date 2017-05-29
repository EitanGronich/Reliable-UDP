from httpservice import HTTPService
from ..Common import constants, util
import urlparse
from dataserver import DataListener

class DataPortService(HTTPService):

    def __init__(self, http_socket, parsedurl):
        super(DataPortService, self).__init__(
            http_socket,
            parsedurl,
        )
        self._qs = urlparse.parse_qs(self._parsedurl.query)
        self.check_query()

    def check_query(self):
        ttl = self._qs["ttl"][0] = util.str_to_float(self._qs["ttl"][0])
        exit_port = self._qs["exit_port"][0] = util.str_to_int(self._qs["exit_port"][0])
        dest_port = self._qs["dest_port"][0] = util.str_to_int(self._qs["dest_port"][0])
        if any(
            [
                a is None for a in (
                    ttl,
                    exit_port,
                    dest_port,
                    util.check_tcp_address(
                        (self._qs["exit_address"][0], exit_port)
                    ),
                )
            ]
        ):
            raise RuntimeError("Invalid Request")

    def prepare_response(self):
        dl = DataListener(
            async_manager=self._http_socket._async_manager,
            bind_address=("0.0.0.0", 0),
            exit_address=(self._qs["exit_address"][0], self._qs["exit_port"][0]),
            dest_address=(self._qs["dest_address"][0], self._qs["dest_port"][0]),
            rudp_manager=self._http_socket._rudp_manager,
            timeout=self._http_socket._timeout,
            block_size=self._http_socket._block_size,
            buff_limit=self._http_socket._buff_limit,
            ttl=self._qs["ttl"][0],
        )
        self._content = constants._FORM_HTML.replace(
            "$port$",
            '<p class="port-info">Your port is: %s.</p>' % dl._s.getsockname()[1],
        )
        self._content_length = len(self._content)
        self._content_type = constants._CONTENT_TYPES[".html"]
        return super(DataPortService, self).prepare_response()

    _FUNCS = {
        HTTPService._RECEIVE_HEADERS: HTTPService.receive_headers,
        HTTPService._OPEN: HTTPService.open,
        HTTPService._PREPARE_RESPONSE: prepare_response,
        HTTPService._SEND_HEADERS: HTTPService.send_headers,
        HTTPService._SEND_CONTENT: HTTPService.send_content,
        HTTPService._CLOSE: HTTPService.close,
        HTTPService._FINISHED: HTTPService.state_finished,
    }
