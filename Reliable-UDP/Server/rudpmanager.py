#!/usr/bin/python

## @package Reliable-UDP.Server.rudpmanager
## @file rudpmanager.py Implementation of @ref Reliable-UDP.Server.rudpmanager

from ..Common import asyncio
import errno
import random
import socket
from ..Common.asyncsocket import AsyncSocket
from rudpconnection import RUDPConnection
from ..Common import constants
import logging

## RUDP Manager
#
# Managers all connections of the server. Opens connections, closes connections
# and also deals with the actual I/O of the UDP socket..
#
class RUDPManager(AsyncSocket):

    ##Init RUDP Manager
    # @param async_manager (Poller) Poller object
    # @param bind_address (tuple) Bind address of UDP socket
    # @param timeout (int) Preferred timeout in milliseconds
    # @param random_drop (int) Percentage chance of dropping a packet
    # @returns (RUDPManager) RUDPManager object
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
        ##Percent chance of dropping a packet
        self._random_drop = random_drop
        ##Dictionary of remote addresses to dictionaries of CID to connection
        #object.
        self._connections_by_rudp_server = {}
        ##List of all connections
        self._connections = []
        ##List of all queued datagrams waiting for send
        self._queued_datagrams = []

    ##Receive read event and apply accoring logic.
    def read(self):
        try:
            string, address = self._s.recvfrom(constants._MAX_RUDP_SIZE)
            d = self.parse_datagram(string)
            logging.info(
                "%s: Received packet from RUDP server %s, with CID %s" % (
                    self,
                    address,
                    d[RUDPConnection._CID]
                )
            )
            r = random.randint(0, 99)
            if r < self._random_drop:
                logging.info(
                    "%s: Packet from server %s, %s: dropped for testing purposes" % (
                        self,
                        address,
                        d[RUDPConnection._CID]
                    )
                )
            else:
                valid = not self._closing
                if address not in self._connections_by_rudp_server:
                    self._connections_by_rudp_server[address] = {}
                if d[RUDPConnection._CID] not in self._connections_by_rudp_server[address]:
                    if d[RUDPConnection._FLAG] != RUDPConnection._FLAG_INIT:
                        logging.info(
                            "%s: Unknown RUDP address %s,%s with non-init flag, discarding packet"
                             % (
                                self,
                                address,
                                d[RUDPConnection._CID]
                            )
                        )
                        valid = False
                    elif d[RUDPConnection._FLAG] == RUDPConnection._FLAG_INIT and d[RUDPConnection._DATA] == "":
                        logging.info(
                            "%s: Unknown RUDP address %s,%s sent connection approval packet, discarding packet"
                             % (
                                self,
                                address,
                                d[RUDPConnection._CID]
                            )
                        )
                        valid = False
                    else:
                        logging.info(
                            "%s: Unknown RUDP address %s,%s with init flag, creating new connection" % (self, address, d[RUDPConnection._CID])
                        )
                        new_connection = RUDPConnection(
                            rudp_manager=self,
                            async_manager=self._async_manager,
                            rudp_peer_address=address,
                            cid=d[RUDPConnection._CID],
                            state=RUDPConnection._INIT_ANSWERER,
                            keep_alive_interval=constants._KEEP_ALIVE_INTERVAL,
                            retry_interval=constants._RETRY_INTERVAL,
                            connection_approval_interval=constants._CONNECTION_APPROVAL_INTERVAL,
                            retry_count=constants._RETRY_COUNT,
                        )
                        self.register_connection(new_connection, d[RUDPConnection._CID])
                if valid:
                    self._connections_by_rudp_server[address][d[RUDPConnection._CID]].receive_datagram(
                        d
                    )
        except IOError as e:
            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise


    ##Queue a datagram for sending
    # @param connection (RUDPConnection) RUDP Connection that's queueing the datagram
    # @param datagram_str (string) Datagram in string form
    # @param datagram_dict (dict) Datagram in dict form
    def queue_datagram(self, connection, datagram_str, datagram_dict):
        self._queued_datagrams.append((connection, datagram_str, datagram_dict))

    ##Receive write event and apply according logic.
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

    ##Parse received datagram
    # @param datagram (string) Datagram in string form
    # @returns (dict) Datagram in dict form
    def parse_datagram(self, datagram):
        d = {}
        for component in RUDPConnection._COMPONENTS:
            d[component] = datagram[:RUDPConnection._LENGTHS[component]]
            if RUDPConnection._TYPES[component] == "int":
                d[component] = int(d[component], 16)
            datagram = datagram[RUDPConnection._LENGTHS[component]:]
        return d

    ##Init connection with remote server by creating Connection object.
    # @param rudp_exit (tuple) Exit server address
    # @param initiator (tuple) Address of initiator user
    # @param endpoint (tuple) Address of endpoint user
    # @param data_socket (DataSocket) DataSocket object connected to
    # initiator user of connection
    def init_connection(self, rudp_exit, initiator, endpoint, data_socket):
        rudp_exit = socket.gethostbyname(rudp_exit)
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
            self.register_connection(new_connection, cid)
            new_connection.connect_to_remote()
            if len(self._connections_by_rudp_server[rudp_exit].keys()) == constants._MAX_CONNECTIONS:
                logging.warning("%s: Maximum number of connections with RUDP server %s reached, accepting no more connections." % (self, rudp_exit))
            return new_connection

    ##Finds the lowest available CID between the server and another RUDP server.
    # @param rudp_exit (tuple) Exit server address
    # @returns (int) CID
    def find_cid(self, rudp_exit):
        for i in range(constants._MAX_CONNECTIONS):
            if i not in self._connections_by_rudp_server[rudp_exit]:
                return i

    ##Registers connection to the existing data structures.
    # @param connection (RUDPConnection) RUDPConnection object.
    # @param cid (int) Connection ID between the two servers
    def register_connection(self, connection, cid):
        self._connections.append(connection)
        self._connections_by_rudp_server[connection._rudp_peer][cid] = connection

    ##Gets the foremost datagram in the queue for sending.
    # @returns (tuple) Datagram tuple consisting of (connection,
    #datagram_str ,datagram_dict)
    def get_datagram_for_send(self):
        d = self._queued_datagrams[0]
        self._queued_datagrams = self._queued_datagrams[1:]
        return d

    #Returns the preferred sleep time of the RUDP Manager.
    # @returns (int) timeout in milliseconds
    def get_sleep_time(self):
        if self._connections:
            return min(
                [c.get_sleep_time() for c in self._connections]
            )
        else:
            return self._timeout

    #Calculates and returns the IO mask for the RUDP Manager.
    # @returns (int) IO mask.
    def get_io_mask(self):
        mask = asyncio.BaseEvent.POLLERR
        if not self._closing:
            mask |= asyncio.BaseEvent.POLLIN
        if self._queued_datagrams:
            mask |= asyncio.BaseEvent.POLLOUT
        return mask

    ##Updates the RUDPManager by updating all RUDPConnection
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

    ##Terminates the RUDP Manager completely.
    def terminate(self):
        for c in self._connections:
            self.close_connection(c)
        super(RUDPManager, self).terminate()

    ##Close connection.
    # @param connection (RUDPConnection) Connection going to be closed
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

    ##Start clean closing sequence
    def init_close(self):
        self._closing = True
        for c in self._connections:
            c.init_close()

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "RUDP Connection Manager (%s)" % self._fileno
