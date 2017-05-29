#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Test_Async.Sender.openlisteningportsocket
# Socket that opens listening port.
## @file openlisteningportsocket.py Implementation of @ref Reliable-UDP.Reliable-UDP.Test_Async.Sender.openlisteningportsocket
#

from ...Common.tcpserver import TCPServerSocket
from ...Common import constants

## Listening Port Opener Socket
#
# Socket that connects to an RUDP Server and asks for
# a port to a certain destination through a certain remote server.
#
class OpenListeningPortSocket(TCPServerSocket):

    ##States of a Listening Port Opener Socket
    _REQUEST_STATES = (
        _SENDING_REQUEST,
        _RECEIVING_PORT,
        _FINISHED,
    ) = range(3)

    def __init__(
        self,
        async_manager,
        timeout,
        block_size,
        buff_limit,
        listening_port_data,
        action,
        args,
        s=None,
        connect_address=None,
    ):
        super(OpenListeningPortSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
            s=s,
            connect_address=connect_address
        )
        self.queue_buffer(
            "op=connect\n"
            "exit_address=%s\n"
            "exit_port=%s\n"
            "dest_address=%s\n"
            "dest_port=%s\n"
            "ttl=0\n"
            "\n" % (
                listening_port_data["exit_address"],
                listening_port_data["exit_port"],
                listening_port_data["dest_address"],
                listening_port_data["dest_port"],
            )
        )
        ##Current state
        self._request_state = self._SENDING_REQUEST
        ##Port to be received from server
        self._port = None
        ##Function object to do once port is obtained
        self._action = action
        ##Arguments to give the function once port is obtained
        self._args=args

    def handle_buf_sent(self, buf):
        if not self._send_buff:
            self._request_state = self._RECEIVING_PORT

    def handle_buf_received(self, buf):
        self._recv_buff += buf
        END = "%s%s" % (constants._LF, constants._LF)
        SEP = "="
        i = buf.find(END)
        if i != -1:
            self._recv_buff = self._recv_buff[:(-len(END))]
            lines = self._recv_buff.split("\n")
            for line in lines:
                field, value = line.split(SEP)
                if field == "code" and int(value) != 0:
                    raise RuntimeError('Request Failed')
                if field == "port":
                    self._port = int(value)
                    self._request_state = self._FINISHED
                    self._action(self, *self._args)
                    self.init_close()

    def receiving(self):
        return self._request_state == self._RECEIVING_PORT and super(OpenListeningPortSocket, self).receiving()

    def init_close(self):
        self._send_buff = ""
        super(OpenListeningPortSocket, self).init_close()

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Listener Socket Opener Socket (%s)" % self._fileno
