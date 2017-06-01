#!/usr/bin/python

## @package Reliable-UDP.Server.rudpconnection
## @file rudpconnection.py Implementation of @ref Reliable-UDP.Server.rudpconnection

from datetime import datetime, timedelta
from dataserver import DataSocket
import random
from ..Common import util
from ..Common import constants
import traceback
import logging

## RUDP Connection Object
#
# Represents a specific connection between a connected user and a remote
# user through a remote server. Handles all logic in the connection,
# incuding timers, retransmits etc.
#
class RUDPConnection(object):
    ##States of an RUDP Connection
    _STATES = (
        _INIT_ANSWERER,
        _INIT_INITIATOR,
        _WAITING_FOR_INIT_ACK,
        _WAITING_CONNECT_STATUS,
        _WAITING_REMOTE_CONNECTION_APPROVAL,
        _WAITING_FOR_ACK,
        _READY_FOR_SEND,
    ) = range(7)
    ##Flags in RUDP Protocol
    _FLAGS = (
        _FLAG_DATA,
        _FLAG_ACK,
        _FLAG_CLOSE,
        _FLAG_INIT,
        _FLAG_KPALIVE,
    ) = (
        0,
        1,
        2,
        4,
        8,
    )
    ##Components of an RUDP packet
    _COMPONENTS = (
        _LENGTH,
        _CID,
        _FLAG,
        _SQN_NUM,
        _DATA,
    ) = range(5)
    ##Map of component to length of that component
    _LENGTHS = {
        _LENGTH: constants._LENGTH_LENGTH,
        _CID: constants._CID_LENGTH,
        _FLAG: constants._FLAG_LENGTH,
        _SQN_NUM: constants._SQN_LENGTH,
        _DATA: constants._DATA_LENGTH,
    }
    ##Map of component to date type of component
    _TYPES = {
        _LENGTH: 'int',
        _CID: 'int',
        _FLAG: 'int',
        _SQN_NUM: 'int',
        _DATA: 'str',
    }

    ##Init RUDPConnection
    # @param rudp_manager (RUDPManager) RUDP Manager object
    # @param async_manager (Poller) Poller object
    # @param rudp_peer_address (tuple) Exit server address
    # @param cid (int) Connection ID
    # @param state (int) Numerical value of starting state
    # @param keep_alive_interval (int) Keep alive interval of connection in milliseconds
    # @param retry_interval (int) Retry interval (RTO) of connection in milliseconds
    # @param connection_approval_interval (int) Connection approval interval
    # of connection in milliseconds
    # @param retry_count (int) Max transmits before exhaustion
    # @param data_socket (DataSocket) Data socket object of the connection
    # @param initiator (tuple) Address of initiator user
    # @param endpoint (tuple) Address of target user
    def __init__(
        self,
        rudp_manager,
        async_manager,
        rudp_peer_address,
        cid,
        state,
        keep_alive_interval,
        retry_interval,
        connection_approval_interval,
        retry_count,
        data_socket=None,
        initiator=None,
        endpoint=None,
    ):
        assert state in (RUDPConnection._INIT_INITIATOR, RUDPConnection._INIT_ANSWERER)
        ##Connection state
        self._connection_state = state
        self._rudp_peer_addr, self._rudp_peer_port = rudp_peer_address
        self._rudp_peer_addr = socket.gethostbyname(self._rudp_peer_addr)
        ##Address of remote RUDP server
        self._rudp_peer = self._rudp_peer_addr, self._rudp_peer_port
        ##RUDP Manager object
        self._rudp_manager = rudp_manager
        ##Async manager object (Poller)
        self._async_manager = async_manager
        ##Sequence number of packets sent
        self._sequence_num = 0
        ##Sequence number of packets received from peer
        self._peer_sequence_num = None
        ##Connection ID
        self._cid = cid
        ##Data socket object
        self._data_socket = data_socket
        ##Retry interval (RTO) of no ack before retransmitting
        self._retry_interval = retry_interval
        ##Retry count before giving up and closing connection
        self._retry_count = retry_count
        ##Keep-alive interval of idle connection
        #before sending keep-alive packet
        self._keep_alive_interval = keep_alive_interval
        ##Connection approval interval - time to wait for connection
        #approval before giving up and closing connection
        self._connection_approval_interval = connection_approval_interval
        if keep_alive_interval == constants._KEEP_ALIVE_INTERVAL:
            self._keep_alive_interval -= random.random() * 1000
        ##Datetime object to send keep-alive
        self._time_send_kp_alive = None
        ##Datetime object to retransmit packet
        self._time_send_retry = None
        ##Datetime object to give up on connection approval
        #and close connection
        self._time_give_up_connection_approval = None
        ##Last non-ack datagram sent - used for retransmissions
        self._last_datagram_sent = None
        ##Buffer to be queued as datagrams
        self._send_buff = ""
        ##Times retrasmitted current packet
        self._times_retried = 0
        ##Overall data bytes sent since beginning of connection
        self._bytes_sent = 0
        ##Overall data bytes received since beginning of connection
        self._bytes_received = 0
        ##Boolean - closing or not
        self._closing = False
        logging.info(
            "%s: Initialized" % self
        )
        if self._connection_state == RUDPConnection._INIT_INITIATOR:
            ##Connected user, the one close to the server
            self._close_user = self._close_user_addr, self._close_user_port = initiator
            ##Remote user, the one connected to the remote server
            self._remote_user = self._remote_user_addr, self._remote_user_port = endpoint

    ##Receive init packet and apply logic.
    # @param d (dict) Init Packet
    def receive_init(self, d):
        if self._connection_state == RUDPConnection._WAITING_REMOTE_CONNECTION_APPROVAL:
            logging.info(
                "%s: Connection to remote user successful, allowing user at %s to send and receive" %(
                    self,
                    self._close_user,
                )
            )
            self._time_give_up_connection_approval = None
            self._connection_state = RUDPConnection._READY_FOR_SEND
        elif self._connection_state == RUDPConnection._INIT_ANSWERER:
            initiator_address, initiator_port, endpoint_addr, endpoint_port = self.parse_init_data(d[RUDPConnection._DATA])
            self._close_user = endpoint_addr, endpoint_port
            self._remote_user = initiator_address, initiator_port
            logging.info(
                "%s: Received request to init connection with %s from RUDP server %s. Trying to connect..." % (
                    self,
                    self._close_user,
                    self._rudp_peer,
                )
            )
            try:
                self._data_socket = DataSocket(
                    async_manager=self._async_manager,
                    rudp_manager=self._rudp_manager,
                    timeout=constants._TIMEOUT,
                    block_size=constants._DATA_BLOCK_SIZE,
                    buff_limit=constants._DATA_BUFF_LIMIT,
                    connect_address=self._close_user,
                    connection=self,
                )
                self._connection_state = RUDPConnection._WAITING_CONNECT_STATUS
            except IOError:
                logging.error(
                    "%s: Failed to initalize connection:\n%s" % (self, traceback.format_exc())
                )
                self.init_close()

    ##Receive data packet and apply logic.
    # @param d (dict) Data Packet
    def receive_data(self, d):
        self._bytes_received += len(d[RUDPConnection._DATA])
        self._data_socket.queue_buffer(d[RUDPConnection._DATA])

    ##Receive ACK packet and apply logic.
    # @param d (dict) ACK Packet
    def receive_ack(self, d):
        if d[RUDPConnection._SQN_NUM] == self._sequence_num:
            if self._connection_state == RUDPConnection._WAITING_FOR_INIT_ACK:
                self._connection_state = RUDPConnection._WAITING_REMOTE_CONNECTION_APPROVAL
                self._time_give_up_connection_approval = datetime.now() + timedelta(microseconds=self._connection_approval_interval * 1000)
                logging.info(
                    "%s: Received init ack" % self
                )
                logging.debug(
                    "%s: Last time set for receiving connection approval: %s" % (
                        self,
                        util.present_datetime(self._time_give_up_connection_approval),
                    )
                )
            else:
                self._connection_state = RUDPConnection._READY_FOR_SEND
            logging.debug(
                "%s: Incremented sequence number from %s to %s" % (self, self._sequence_num, self._sequence_num + 1)
            )
            self._sequence_num += 1
            self._times_retried = 0
            self._time_send_retry = None

    ##Receive close packet and apply logic.
    # @param d (dict) Close Packet
    def receive_close(self, d):
        if self._connection_state == RUDPConnection._WAITING_FOR_INIT_ACK:
            logging.info(
                "%s: Connection process to user %s through %s unsucessful, closing connection with user %s" % (
                    self,
                    self._remote_user,
                    self._rudp_peer,
                    self._close_user,
                )
            )
        else:
            logging.info(
                "%s: Received a closing packet, closing connection..." % self
            )
        self.init_close(queue_close=False)

    ##Receive keep-alive packet and apply logic.
    # @param d (dict) Keep-alive Packet
    def receive_kpalive(self, d):
        pass

    ##Dict of flag type received to method
    _RECV_FUNCS = {
        _FLAG_INIT: receive_init,
        _FLAG_CLOSE: receive_close,
        _FLAG_DATA: receive_data,
        _FLAG_ACK: receive_ack,
        _FLAG_KPALIVE: receive_kpalive,
    }

    ##Queue closing packet.
    def queue_close(self):
        self.queue_datagram(
            RUDPConnection._FLAG_CLOSE,
            self._sequence_num,
            "",
        )

    ##Init closing sequence of connection.
    # @param queue_close (bool) Queue closing packet or not
    def init_close(self, queue_close=True):
        self._closing = True
        if self._data_socket and not self._data_socket._closing:
            self._data_socket.init_close()
        self._data_socket = None
        if queue_close:
            self.queue_close()
        self._rudp_manager.close_connection(self)

    ##Logic when data connection to user is successful.
    def approve_data_socket(self):
        logging.info(
            "%s: Connection to user %s sucessful, completing connection process with %s" % (
                self,
                self._close_user,
                self._rudp_peer,
            )
        )
        self.queue_datagram(
            flag=RUDPConnection._FLAG_INIT,
            sqn_num=self._sequence_num,
            data="",
        )

    ##Parse data of Init packet.
    # @param data (string) Init data
    # @returns (tuple) Initiator address, initiator port, endpoint address,
    # endpoint port
    def parse_init_data(self, data):
        data = data.split("\n")
        if len(data) != 5:
            raise RuntimeError("Invalid init data")
        data = data[:4]
        data = [d.split(":")[1] for d in data]
        return (
            data[0],
            int(data[1]),
            data[2],
            int(data[3]),
        )

    #Send datagram to RUDP Manager to queue.
    # @param flag (int) Flag of packet
    # @param sqn_num (int) Sequence num of packet
    # @param data (string) Data of packet
    # @param retry (bool) Whether this is retry or not
    def queue_datagram(self, flag, sqn_num, data, retry=False):
        content = "%04x%01x%04x%s" %(
                    self._cid,
                    flag,
                    sqn_num,
                    data,
        )
        params = {
            RUDPConnection._FLAG: flag,
            RUDPConnection._SQN_NUM: sqn_num,
            RUDPConnection._DATA: data,
            "Retry": retry
        }
        datagram = "%04x%s" % (
            len(content),
            content,
        )
        self._rudp_manager.queue_datagram(
            self,
            datagram,
            params,
        )
        if flag == RUDPConnection._FLAG_INIT:
            if data == "":
                self._connection_state = RUDPConnection._WAITING_FOR_ACK
            else:
                self._connection_state = RUDPConnection._WAITING_FOR_INIT_ACK
        elif flag != RUDPConnection._FLAG_ACK:
            self._connection_state = RUDPConnection._WAITING_FOR_ACK
        if retry:
            self._times_retried += 1

    ##Logic when datagram is sent from queue in RUDPManager.
    # @param datagram (string) Datagram in string form
    # @param params (dict) Parts of the datagram
    def datagram_sent(self, datagram, params):
        logging.info(
            (
                "%s: Datagram sent: Flag: %s; Sequence number: %s; Data: %s"
            ) % (
                self,
                params[RUDPConnection._FLAG],
                params[RUDPConnection._SQN_NUM],
                params[RUDPConnection._DATA],
            )
        )
        if params[RUDPConnection._FLAG] == RUDPConnection._FLAG_DATA:
            self._bytes_sent += len(params[RUDPConnection._DATA])
        self._time_send_kp_alive = datetime.now() + timedelta(microseconds=self._keep_alive_interval*1000)
        logging.debug(
            "%s: Time to send keep-alive set to %s" % (self, util.present_datetime(self._time_send_kp_alive))
        )
        flag = params[RUDPConnection._FLAG]
        if flag != RUDPConnection._FLAG_ACK:
            self._last_datagram_sent = datagram, params
            self._time_send_retry = datetime.now() + timedelta(microseconds=self._retry_interval*1000)
            logging.debug(
                "%s: Time to resend packet set to %s" % (self, util.present_datetime(self._time_send_retry))
            )
        if params["Retry"]:
            logging.info(
                "%s: No acknowledgement received from peer, resent packet for the %s time out of %s"
                 % (
                    self,
                    self._times_retried,
                    self._retry_count
                )
            )

    ##Receive packet and apply general logic before splitting
    #into specific methods.
    # @param d (dict) Parts of the packet.
    def receive_datagram(self, d):
        self._time_send_kp_alive = datetime.now() + timedelta(microseconds=self._keep_alive_interval*1000)
        logging.debug(
            "%s: Time to set keep-alive set to %s" % (self, util.present_datetime(self._time_send_kp_alive))
        )
        logging.info(
            (
                "%s: Datagram received: Flag: %s; Sequence number: %s; Data: %s"
            ) % (
                self,
                d[RUDPConnection._FLAG],
                d[RUDPConnection._SQN_NUM],
                d[RUDPConnection._DATA],
            )
        )
        if d[RUDPConnection._FLAG] == RUDPConnection._FLAG_ACK:
            self.receive_ack(d)
        elif d[RUDPConnection._FLAG] == RUDPConnection._FLAG_INIT and self._connection_state == RUDPConnection._WAITING_FOR_INIT_ACK:
            logging.info("%s: Received connection approval before init ack, init ack probably lost")
        else:
            duplicate = False
            if self._peer_sequence_num is None:
                self._peer_sequence_num = d[RUDPConnection._SQN_NUM]
            elif d[RUDPConnection._SQN_NUM] <= self._peer_sequence_num:
                duplicate = True
            if not duplicate:
                self._RECV_FUNCS[d[RUDPConnection._FLAG]](self, d)
                self._peer_sequence_num = d[RUDPConnection._SQN_NUM]
            else:
                logging.info(
                    "%s: Sequence num of received packet: %s, highest sequence num already received: %s, discarding duplicate packet"
                     % (
                        self,
                        d[RUDPConnection._SQN_NUM],
                        self._peer_sequence_num,
                    )
                )
            if d[RUDPConnection._FLAG] not in (RUDPConnection._FLAG_ACK, RUDPConnection._FLAG_CLOSE):
                self.queue_ack()

    ##Start the connection sequence with a remote server.
    def connect_to_remote(self):
        logging.info(
            "%s: Trying to connect to %s through %s, waiting for response" % (
                self,
                self._remote_user,
                self._rudp_peer,
            )
        )
        self.queue_datagram(
            RUDPConnection._FLAG_INIT,
            self._sequence_num,
            (
                "Source Address:%s\n"
                "Source Port:%s\n"
                "Destination Address:%s\n"
                "Destination Port:%s\n"
            ) % (
                self._close_user_addr,
                self._close_user_port,
                self._remote_user_addr,
                self._remote_user_port,
            )
        )

    ##Queue a TCP buffer received from user, to be sent
    #as datagram.
    # @param buf (string) TCP buffer
    def queue_buffer(self, buf):
        self._send_buff += buf
        self.queue_datagram(
            RUDPConnection._FLAG_DATA,
            self._sequence_num,
            self._send_buff[:constants._DATA_LENGTH],
        )
        self._send_buff = self._send_buff[constants._DATA_LENGTH:]

    ##Returns preferred sleep time based on protocol timeouts.
    # @returns (int) sleep time in milliseconds
    def get_sleep_time(self):
        t = constants._TIMEOUT
        if self._time_send_kp_alive:
            t_until_kp_alive = ((self._time_send_kp_alive - datetime.now()).total_seconds()) * 1000.0
            t = min(t, t_until_kp_alive)
        if self._time_give_up_connection_approval:
            t_until_give_up = ((self._time_give_up_connection_approval - datetime.now()).total_seconds()) * 1000.0
            t = min(t, t_until_give_up)
        if self._time_send_retry:
            t_until_retry = ((self._time_send_retry - datetime.now()).total_seconds()) * 1000.0
            t = min(t, t_until_retry)
        return t

    ##Queues ack packet.
    def queue_ack(self):
        self.queue_datagram(
            RUDPConnection._FLAG_ACK,
            self._peer_sequence_num,
            ""
        )

    ##Queues keep-alive packet.
    def queue_kp_alive(self):
        self.queue_datagram(
            RUDPConnection._FLAG_KPALIVE,
            self._sequence_num,
            ""
        )

    ##Retry sending the last non-ack packet sent.
    def retry_send(self):
        datagram, params = self._last_datagram_sent
        self.queue_datagram(
            flag=params[RUDPConnection._FLAG],
            sqn_num=params[RUDPConnection._SQN_NUM],
            data=params[RUDPConnection._DATA],
            retry=True,
        )

    ##Update protocol intervals and apply logic accordingly.
    def update(self):
        now = datetime.now()
        if self._time_send_kp_alive is not None and now >= self._time_send_kp_alive:
            self.queue_kp_alive()
        if self._time_give_up_connection_approval and now >= self._time_give_up_connection_approval:
            logging.info(
                "%s: Peer not approving connection, closing connection..." % self
            )
            self.init_close()
        if self._time_send_retry is not None and now >= self._time_send_retry and self._connection_state in (RUDPConnection._WAITING_FOR_ACK, RUDPConnection._WAITING_FOR_INIT_ACK):
            if self._times_retried >= self._retry_count:
                logging.info(
                    "%s: Peer not answering packets, closing connection..." % self
                )
                self.init_close(queue_close=False)
            else:
                self.retry_send()
        if self._connection_state == RUDPConnection._READY_FOR_SEND and self._send_buff:
            self.queue_buffer('')

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Connection (%s, %s), %s" % (self._rudp_peer_addr, self._rudp_peer_port, self._cid)
