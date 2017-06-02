#!/usr/bin/python

## @package Reliable-UDP.Server.blankservice
## @file blankservice.py Implementation of @ref Reliable-UDP.Server.blankservice

from httpservice import HTTPService
from ..Common import constants

## Service of blank url, redirects to home page
#
#
class BlankService(HTTPService):

    ##Inits BlankService
    # @param http_socket (HTTP Socket) HTTP Socket object
    # @param parsedurl (urlparse.ParseResult) parsedl url
    # @returns (BlankService) BlankService object
    def __init__(self, http_socket, parsedurl):
        super(BlankService, self).__init__(
            http_socket,
            parsedurl,
        )

    ##Prepare response
    # @return (bool) Response prepared or not
    def prepare_response(self):
        self._headers_out["Location"] = "/home.html"
        self._http_socket.send_headers(
            code=constants._HTTP_REDIRECT,
            message=constants._HTTP_REDIRECT_MESSAGE,
            headers=self._headers_out,
        )
        self._state = self._SEND_CONTENT
        self._sent = True
        return True

    ##Dict of states to mathing methods
    _FUNCS = {
        HTTPService._RECEIVE_HEADERS: HTTPService.receive_headers,
        HTTPService._OPEN:  HTTPService.open,
        HTTPService._PREPARE_RESPONSE: prepare_response,
        HTTPService._SEND_HEADERS:  HTTPService.send_headers,
        HTTPService._SEND_CONTENT:  HTTPService.send_content,
        HTTPService._CLOSE:  HTTPService.close,
        HTTPService._FINISHED:  HTTPService.state_finished,
    }
