#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Server.connectionsservice
## @file connectionsservice.py Implementation of @ref Reliable-UDP.Reliable-UDP.Server.connectionsservice

from httpservice import HTTPService
from ..Common import constants

## Connection Data Service
#
# HTTP Service that services the HTTP page with data about connections.
#
class ConnectionsService(HTTPService):

    ##Inits Connections Service
    # @param http_socket (http_socket) HTTP Socket object
    # @param  parsedurl (urlparse.ParseResult) parsed url
    # @returns (ConnectionsService) Connections Service object
    def __init__(self, http_socket, parsedurl):
        super(ConnectionsService, self).__init__(
            http_socket,
            parsedurl,
        )

    ##Prepares response for send
    # @returns (bool) finished preparing or not
    def prepare_response(self):
        self._content = constants._CONNECTIONS_HTML
        table_data = ""
        for c in self._http_socket._rudp_manager._connections:
            table_data += (
                """
                    <tr>
                        <td class="table-data">%s, %s</td>
                        <td class="table-data">%s</td>
                        <td class="table-data">%s</td>
                        <td class="table-data">%s</td>
                        <td class="table-data">%s</td>
                        <td class="table-data">%s</td>
                        <td class="table-data">%s</td>
                    </tr>
                """ % (
                    c._rudp_peer,
                    c._cid,
                    c._close_user,
                    c._remote_user,
                    c._bytes_sent,
                    c._bytes_received,
                    c._sequence_num,
                    c._peer_sequence_num,
                )
            )
        self._content = self._content.replace(
            "$data$",
            table_data
        )
        self._content_length = len(self._content)
        self._content_type = constants._CONTENT_TYPES[".html"]
        return super(ConnectionsService, self).prepare_response()

    ##Dictionary of states to matching methods
    _FUNCS = {
        HTTPService._RECEIVE_HEADERS: HTTPService.receive_headers,
        HTTPService._OPEN: HTTPService.open,
        HTTPService._PREPARE_RESPONSE: prepare_response,
        HTTPService._SEND_HEADERS: HTTPService.send_headers,
        HTTPService._SEND_CONTENT: HTTPService.send_content,
        HTTPService._CLOSE: HTTPService.close,
        HTTPService._FINISHED: HTTPService.state_finished,
    }
