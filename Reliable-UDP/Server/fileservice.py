#!/usr/bin/python

## @package Reliable-UDP.Server.fileservice
## @file fileservice.py Implementation of @ref Reliable-UDP.Server.fileservice


from httpservice import HTTPService
import httpserver
import os
from ..Common import constants
import errno

## File Service
#
# HTTP Service that services static files.
#
class FileService(HTTPService):

    ##Init FileService
    # @param http_socket (HTTPSocket) HTTP Socket Object
    # @param parsedurl (urlparse.ParseResult) Parsed request URL
    # @returns (FileService) File Service Object
    def __init__(self, http_socket, parsedurl):
        super(FileService, self).__init__(
            http_socket,
            parsedurl,
        )
        ##File descriptor to read requested file
        self._fd = None

    ##Open file requested.
    # @returns (bool) File opened or not
    def open(self):
        ##Filename of requested file
        self._filename = os.path.normpath(
            os.path.join(
                constants._BASE_DIRECTORY,
                self._parsedurl.path[1:],
            )
        )
        try:
            self._fd = os.open(
                self._filename,
                os.O_RDONLY,
                0o666,
            )
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise httpserver.HTTPError(
                    code=constants._HTTP_FILE_NOT_FOUND,
                    message="File Not Found",
                )
        return super(FileService, self).open()

    ##Prepare request reponse.
    # @returns (bool) Response prepared or not
    def prepare_response(self):
        self._content_length = os.fstat(self._fd).st_size
        self._content_type = constants._CONTENT_TYPES[
            os.path.splitext(self._filename)[1]
        ]
        return super(FileService, self).prepare_response()

    ##Send response content
    # @returns (bool) Response content sent or not
    def send_content(self):
        while True:
            if len(self._http_socket._send_buff) >= constants._HTTP_BUFF_LIMIT:
                return
            buf = os.read(
                self._fd,
                constants._FILE_BLOCK_SIZE,
            )
            if not buf:
                return super(FileService, self).send_content()
            self._http_socket.queue_buffer(buf)

    ##Closes requested file.
    # @returns (bool) File closed or not
    def close(self):
        if self._fd:
            os.close(self._fd)
        return super(FileService, self).close()

    ##Dictionary of states to methods
    _FUNCS = {
        HTTPService._RECEIVE_HEADERS: HTTPService.receive_headers,
        HTTPService._OPEN: open,
        HTTPService._PREPARE_RESPONSE: prepare_response,
        HTTPService._SEND_HEADERS:  HTTPService.send_headers,
        HTTPService._SEND_CONTENT: send_content,
        HTTPService._CLOSE: close,
        HTTPService._FINISHED: HTTPService.state_finished,
    }
