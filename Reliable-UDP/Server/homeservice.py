from httpservice import HTTPService
from ..Common import constants

class HomeService(HTTPService):

    def __init__(self, http_socket, parsedurl):
        super(HomeService, self).__init__(
            http_socket,
            parsedurl,
        )

    def prepare_response(self):
        self._content = (
            """
                <html>
                    <head>
                        <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
                        <meta http-equiv="refresh" content=10>
                    </head>
                    <body>
                        <h1>Reliable UDP Server</h1>
                        <h2>Connection Data</h2>
                        <table style="width:50%">
                        <tr>
                            <th>Address, CID</th>
                            <th>Bytes Sent</th>
                        </tr>
            """
        )
        for c in self._http_socket._rudp_manager._connections:
            self._content += (
                """
                    <tr>
                        <td>%s, %s</td>
                        <td> %s </td>
                    </tr>
                """ % (
                    c._rudp_peer,
                    c._cid,
                    c._bytes_sent,
                )
            )
        self._content += (
            """
                </table>
                <form action="connect_request.html" target="_blank">
                    <input type="submit" value="Add A Connection"/>
                </form>
                </body>
                </html>
            """
        )
        self._content_length = len(self._content)
        self._content_type = constants._CONTENT_TYPES[".html"]
        return super(HomeService, self).prepare_response()

    _FUNCS = {
        HTTPService._RECEIVE_HEADERS: HTTPService.receive_headers,
        HTTPService._OPEN: HTTPService.open,
        HTTPService._PREPARE_RESPONSE: prepare_response,
        HTTPService._SEND_HEADERS: HTTPService.send_headers,
        HTTPService._SEND_CONTENT: HTTPService.send_content,
        HTTPService._CLOSE: HTTPService.close,
        HTTPService._FINISHED: HTTPService.state_finished,
    }
