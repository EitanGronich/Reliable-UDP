#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Server.httpserver
## @file httpserver.py Implementation of @ref Reliable-UDP.Reliable-UDP.Server.httpserver

import traceback
from ..Common import util
from ..Common.tcpserver import TCPServerSocket, TCPServerListener
import urlparse
from fileservice import FileService
from dataportservice import DataPortService
from connectionsservice import ConnectionsService
from ..Common import constants
import logging

## HTTP Error
#
# Inherits from RuntimeError, indicates error with HTTP Protocol.
# Could be for example 404 File not Found or 500 Internal Error.
#
class HTTPError(RuntimeError):
   def __init__(self, code, message, headers={}, content=''):
       super(HTTPError, self).__init__(message)
       ##Message of HTTP Error
       self.message = message
       ##Code of HTTP Error
       self.code = code
       ##Headers of HTTP Error
       self.headers = headers
       ##Content of HTTP Error
       self.content = content

   def code(self):
       return self.code

   def message(self):
       return self.message

   def headers(self):
       return self.headers

   def content(self):
       return self.content

## HTTP Socket
#
# Inherits from TCPServerSocket, deals with data sent and received from browsers
# in the HTTP protocol.
#
class HTTPSocket(TCPServerSocket):

    """
        Class of sockets that handle http
        connection with clients. This kind of connection
        facilitates the user asking for connections and also
        for statistics.
    """

    ##Dictionary of URI's to services. File uri's are not None
    #but are incorporated into "None" category
    _SERVICES = {
        None: FileService,
        "/return_port": DataPortService,
        "/connections": ConnectionsService,
    }

    def __init__(
            self,
            async_manager,
            rudp_manager,
            timeout,
            socket,
            block_size,
            buff_limit,
        ):
        super(HTTPSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            s=socket,
            block_size=block_size,
            buff_limit=buff_limit,
        )
        ##RUDP Manager object
        self._rudp_manager = rudp_manager
        ##Current service
        self._service = None

    def handle_buf_received(self, buf):
        self._recv_buff += buf
        self.parse_buffer()

    def parse_buffer(self):
        if self._service:
            try:
                self._service.parse_buffer(self._recv_buff)
            except Exception as e:
                logging.error(
                    "%s: %s" % (self, traceback.format_exc())
                )
                if not self._service._sent:
                    self.send_error(e)
                self._service.close()

            if self._service.finished():
                self.init_close()
                self._service = None
                self._recv_buff = ""

        else:
            try:
                if self.parse_status():
                    service = None
                    for k in HTTPSocket._SERVICES:
                        if k and self._parsedurl.path == k:
                            service = k
                    self._service = HTTPSocket._SERVICES[service](self, self._parsedurl)
                    self.parse_buffer()
            except Exception as e:
                logging.error(
                    "%s: %s" % (self, traceback.format_exc())
                )
                self.send_error(e)

    def parse_status(self):
        status, self._recv_buff = util.split_buffer(self._recv_buff, constants._CRLF_BIN)
        if not status:
            return
        status_comps = status.split(' ', 2)
        if status_comps[2] != constants._HTTP_SIGNATURE:
            raise RuntimeError('Not HTTP protocol')
        if len(status_comps) != 3:
            raise RuntimeError('Incomplete HTTP protocol')
        method, uri, signature = status_comps
        if method != 'GET':
            raise RuntimeError(
                "HTTP unsupported method '%s'" % method
            )
        if not uri or uri[0] != '/':
            raise RuntimeError("Invalid URI")
        self._parsedurl = urlparse.urlparse(uri)
        return True

    def send_error(self, e):
        if type(e).__name__ == "HTTPError":
            code = e.code
            message = e.message
            headers = e.headers
            content = e.content
        else:
            code = constants._HTTP_INTERNAL_ERROR
            message = "Internal Error"
            headers = {}
            content = ""
        self.send_headers(
            code=code,
            message=message,
            content_type='text/plain',
            content_length=len(content),
            headers=headers,
        )
        self.queue_buffer(content)
        self.init_close()

    def send_headers(self, code, message, content_type, content_length, headers):
        self.queue_buffer(
            (
                '%s %s %s\r\n'
                'Content-Type: %s\r\n'
                'Content-Length: %s\r\n'
            ) % (
                constants._HTTP_SIGNATURE,
                code,
                message,
                content_type,
                content_length,
            )
        )
        for k, v in headers.items():
            self.queue_buffer(
                '%s: %s\r\n' % (
                    k,
                    v,
                )
            )
        self.queue_buffer(constants._CRLF_BIN)

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "HTTP Socket (%s)" % self._fileno

## HTTP Listener Socket
#
# Inherits from TCPServerListener, only listens for connections and makes
# HTTP sockets.
#
class HTTPListener(TCPServerListener):

    """
        Class of listener sockets that accept
        HTTP connections, through which users ask for connections in a
        nice looking user interface, and also ask
        for statistics.
    """

    def __init__(
        self,
        bind_address,
        async_manager,
        rudp_manager,
        timeout,
        block_size,
        buff_limit,
    ):
        super(HTTPListener, self).__init__(
            bind_address=bind_address,
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
        )
        ##RUDP Manager object
        self._rudp_manager = rudp_manager

    def read(self):
        s1 = None
        try:
            s1, addr = self._s.accept()
            logging.info(
                "%s: HTTP Connection accepted from %s" % (self, s1.getpeername())
            )
            s1.setblocking(0)
            HTTPSocket(
                async_manager=self._async_manager,
                rudp_manager=self._rudp_manager,
                timeout=self._timeout,
                socket=s1,
                block_size=self._block_size,
                buff_limit=self._buff_limit,
            )
        except IOError:
            logging.error(
                "%s: Failed to initalize connection:\n%s" % (self, traceback.format_exc())
            )
            if s1:
                s1.close()

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "HTTP Listener Socket (%s)" % self._fileno
