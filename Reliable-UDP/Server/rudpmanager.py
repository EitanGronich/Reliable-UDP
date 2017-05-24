#!/usr/bin/python

from ..Common import asyncio
import errno
import random
import socket
from ..Common.asyncsocket import AsyncSocket
from rudpconnection import RUDPConnection
from ..Common import constants
import logging

class RUDPManager(AsyncSocket):
    _COMPONENTS = (
        _LENGTH,
        _CID,
        _FLAG,
        _DATAGRAM
    ) = range(4)
    _LENGTHS = {
        _LENGTH: constants._LENGTH_LENGTH,
        _CID: constants._CID_LENGTH,
        _FLAG: constants._FLAG_LENGTH,
        _DATAGRAM: constants._SQN_LENGTH + constants._DATA_LENGTH,
    }
    _TYPES = {
        _LENGTH: 'int',
        _CID: 'int',
        _FLAG: 'int',
        _DATAGRAM: 'str',
    }

    def __init__(
        self,
        async_manager,
        bind_address,
        timeout,
        random_drop,
    ):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
        )
        s.setblocking(0)
        s.bind(bind_address)
        super(RUDPManager, self).__init__(
            async_manager=async_manager,
            socket=s,
            timeout=timeout,
        )
        self._random_drop = random_drop
        self._connections_by_rudp_server = {}
        self._connections = []
        self._queued_datagrams = []

    def read(self):
        try:
            string, address = self._s.recvfrom(constants._MAX_RUDP_SIZE)
            d = self.parse_datagram(string)
            logging.info(
                "%s: Received packet from RUDP server %s, with CID %s" % (
                    self,
                    address,
                    d[RUDPManager._CID]
                )
            )
            r = random.randint(0, 99)
            if r < self._random_drop:
                logging.info(
                    "%s: Packet from server %s, CID %s dropped for testing purposes" % (
                        self,
                        address,
                        d[RUDPManager._CID]
                    )
                )
            else:
                valid = not self._closing
                if address not in self._connections_by_rudp_server:
                    self._connections_by_rudp_server[address] = {}
                if d[RUDPManager._CID] not in self._connections_by_rudp_server[address]:
                    if d[RUDPManager._FLAG] != RUDPConnection._FLAG_INIT:
                        logging.info(
                            "%s: Unknown RUDP address %s,%s with non-init flag, discarding packet"
                             % (
                                self,
                                address,
                                d[RUDPManager._CID]
                            )
                        )
                        valid = False
                    else:
                        logging.info(
                            "%s: Unknown RUDP address %s,%s with init flag, creating new connection" % (self, address, d[RUDPManager._CID])
                        )
                        new_connection = RUDPConnection(
                            rudp_manager=self,
                            async_manager=self._async_manager,
                            rudp_peer_address=address,
                            cid=d[RUDPManager._CID],
                            state=RUDPConnection._INIT_ANSWERER,
                            keep_alive_interval=constants._KEEP_ALIVE_INTERVAL,
                            retry_interval=constants._RETRY_INTERVAL,
                            connection_approval_interval=constants._CONNECTION_APPROVAL_INTERVAL,
                            retry_count=constants._RETRY_COUNT,
                        )
                        self.register_connection(new_connection, address, d[RUDPManager._CID])
                if valid:
                    self._connections_by_rudp_server[address][d[RUDPManager._CID]].receive_datagram(
                        "%s%s" % (
                            d[RUDPManager._FLAG],
                            d[RUDPManager._DATAGRAM]
                        )
                    )
        except IOError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise


    def queue_datagram(self, connection, datagram_str, datagram_dict):
        self._queued_datagrams.append((connection, datagram_str, datagram_dict))

    def write(self):
        try:
            while self._queued_datagrams:
                d = self.get_datagram_for_send()
                connection, datagram, params = d[0], d[1], d[2]
                self._s.sendto(
                    datagram,
                    connection._rudp_peer,
                )
                connection.datagram_sent(datagram, params)
        except IOError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise

    def parse_datagram(self, datagram):
        d = {}
        for component in RUDPManager._COMPONENTS:
            d[component] = datagram[:RUDPManager._LENGTHS[component]]
            if RUDPManager._TYPES[component] == "int":
                d[component] = int(d[component], 16)
            datagram = datagram[RUDPManager._LENGTHS[component]:]
        return d

    def init_connection(self, rudp_exit, initiator, endpoint, data_socket):
        if rudp_exit not in self._connections_by_rudp_server:
            self._connections_by_rudp_server[rudp_exit] = {}
        cid = self.find_cid(rudp_exit)
        if cid is None:
            logging.warning(
                "%s: Couldn't accept connection, maximum connections reached" % self
            )
            data_socket.init_close()
        else:
            logging.info(
                (
                    "%s: Creating new connection: RUDP Peer: %s; CID: %s; Initiating user: %s; Target user: %s"
                )% (
                    self,
                    rudp_exit,
                    cid,
                    initiator,
                    endpoint,
                )
            )
            new_connection = RUDPConnection(
                rudp_manager=self,
                async_manager=self._async_manager,
                rudp_peer_address=rudp_exit,
                cid=cid,
                state=RUDPConnection._INIT_INITIATOR,
                keep_alive_interval=constants._KEEP_ALIVE_INTERVAL,
                retry_interval=constants._RETRY_INTERVAL,
                connection_approval_interval=constants._CONNECTION_APPROVAL_INTERVAL,
                retry_count=constants._RETRY_COUNT,
                initiator=initiator,
                endpoint=endpoint,
                data_socket=data_socket,
            )
            self.register_connection(new_connection, rudp_exit, cid)
            new_connection.connect_to_remote()
            if len(self._connections_by_rudp_server[rudp_exit].keys()) == constants._MAX_CONNECTIONS:
                logging.warning("%s: Maximum number of connections with RUDP server %s reached, accepting no more connections." % (self, rudp_exit))
            return new_connection


    def find_cid(self, rudp_exit):
        for i in range(constants._MAX_CONNECTIONS):
            if i not in self._connections_by_rudp_server[rudp_exit]:
                return i

    def register_connection(self, connection, rudp_exit, cid):
        self._connections.append(connection)
        self._connections_by_rudp_server[rudp_exit][cid] = connection

    def get_datagram_for_send(self):
        '''
            Returns datagram for sending.
        '''
        d = self._queued_datagrams[0]
        self._queued_datagrams = self._queued_datagrams[1:]
        return d

    def get_sleep_time(self):
        if self._connections:
            return min(
                [c.get_sleep_time() for c in self._connections]
            )
        else:
            return self._timeout

    def get_io_mask(self):
        mask = asyncio.BaseEvent.POLLERR
        if not self._closing:
            mask |= asyncio.BaseEvent.POLLIN
        if self._queued_datagrams:
            mask |= asyncio.BaseEvent.POLLOUT
        return mask

    def is_alive(self):
        return True

    def update(self):
        for c in self._connections:
            c.update()
        if all(
            (
                self._closing,
                not self._connections,
                not self._queued_datagrams,
            )
        ):
            self.terminate()

    def terminate(self):
        for c in self._connections:
            self.close_connection(c)
        super(RUDPManager, self).terminate()

    def close_connection(self, connection):
        logging.info(
            "%s: Connection %s, %s closed" % (self, connection._rudp_peer, connection._cid)
        )
        if len(self._connections_by_rudp_server[connection._rudp_peer].keys()) == constants._MAX_CONNECTIONS:
            if not self._closing:
                logging.warning(
                    "%s: Accepting connections through RUDP server %s again" % (self, connection._rudp_peer)
                )
        try:
            del self._connections_by_rudp_server[connection._rudp_peer][connection._cid]
            self._connections.remove(connection)
        except (ValueError, KeyError):
            pass

    def init_close(self):
        self._closing = True
        for c in self._connections:
            c.init_close()

    def __repr__(self):
        return "RUDP Connection Manager (%s)" % self._fileno