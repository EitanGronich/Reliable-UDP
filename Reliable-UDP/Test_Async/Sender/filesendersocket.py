#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Test_Async.Sender.filesendersocket
## @file filesendersocket.py Implementation of @ref  Reliable-UDP.Reliable-UDP.Test_Async.Sender.filesendersocket

from ...Common.tcpserver import TCPServerSocket
import os
import logging

## File Sender Socket
#
# Sends a file in blocks to a destination and expects
# to receive the exact same things back. If not, or if
# disconnected prematurely, raises error.
#
class FileSenderSocket(TCPServerSocket):

    ##States of a file sender object
    _FILE_SEND_STATES = (
        _SENDING_BLOCK,
        _RECEIVING_BLOCK,
        _FINISHED,
    ) = range(3)

    def __init__(
        self,
        async_manager,
        timeout,
        block_size,
        buff_limit,
        file_to_send,
        s=None,
        connect_address=None,
    ):
        ##Current state
        self._file_send_state = self._SENDING_BLOCK
        ##Last buffer sent
        self._buf_sent = None
        ##File descriptor of file to be sent
        self._fd = os.open(
            file_to_send,
            os.O_RDONLY,
            0o666,
        )
        super(FileSenderSocket, self).__init__(
            async_manager=async_manager,
            timeout=timeout,
            block_size=block_size,
            buff_limit=buff_limit,
            s=s,
            connect_address=connect_address
        )
        self.queue_file_block()

    def handle_buf_sent(self, buf):
        if not self._send_buff:
            self._file_send_state = self._RECEIVING_BLOCK

    def handle_buf_received(self, buf):
        self._recv_buff += buf
        if len(self._recv_buff) >= len(self._buf_sent):
            if self._recv_buff != self._buf_sent:
                logging.error(
                    "%s, socket port %s, false data received, sent %s, received %s"
                     % (self, self._s.getsockname()[1], self._buf_sent, self._recv_buff)
                )
                raise RuntimeError('Bad Data')
            self._recv_buff = ""
            self.queue_file_block()

    def queue_file_block(self):
        send_buf = os.read(self._fd, self._block_size)
        if not send_buf:
            self._file_send_state = self._FINISHED
            self.init_close()
        else:
            self.queue_buffer(send_buf)
            self._buf_sent = send_buf
            self._file_send_state = self._SENDING_BLOCK

    def receiving(self):
        return self._file_send_state == self._RECEIVING_BLOCK and super(FileSenderSocket, self).receiving()

    def terminate(self):
        if self._file_send_state != self._FINISHED:
            logging.error("%s: terminated but not finished" % self)
        os.close(self._fd)
        super(FileSenderSocket, self).terminate()

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "File Sender Socket (%s)" % self._fileno
