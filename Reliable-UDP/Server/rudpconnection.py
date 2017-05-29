#!/usr/bin/python

from datetime import datetime, timedelta
from dataserver import DataSocket
import random
from ..Common import util
from ..Common import constants
import traceback
import logging

class RUDPConnection(object):
    _STATES = (
        _INIT_ANSWERER,
        _INIT_INITIATOR,
        _WAITING_FOR_INIT_ACK,
        _WAITING_CONNECT_STATUS,
        _WAITING_REMOTE_CONNECTION_APPROVAL,
        _WAITING_FOR_ACK,
        _READY_FOR_SEND,
    ) = range(7)
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
    _COMPONENTS = (
        _LENGTH,
        _CID,
        _FLAG,
        _SQN_NUM,
        _DATA,
    ) = range(5)
    _LENGTHS = {
        _LENGTH: constants._LENGTH_LENGTH,
        _CID: constants._CID_LENGTH,
        _FLAG: constants._FLAG_LENGTH,
        _SQN_NUM: constants._SQN_LENGTH,
        _DATA: constants._DATA_LENGTH,
    }
    _TYPES = {
        _LENGTH: 'int',
        _CID: 'int',
        _FLAG: 'int',
        _SQN_NUM: 'int',
        _DATA: 'str',
    }

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
        self._connection_state = state
        self._rudp_peer = self._rudp_peer_addr, self._rudp_peer_port = rudp_peer_address
        self._rudp_manager = rudp_manager
        self._async_manager = async_manager
        self._sequence_num = 0
        self._peer_sequence_num = None
        self._cid = cid
        self._data_socket = data_socket
        self._retry_interval = retry_interval
        self._retry_count = retry_count
        self._keep_alive_interval = keep_alive_interval
        self._connection_approval_interval = connection_approval_interval
        if keep_alive_interval == constants._KEEP_ALIVE_INTERVAL:
            self._keep_alive_interval -= random.random() * 1000
        self._time_send_kp_alive = None
        self._time_send_retry = None
        self._time_give_up_connection_approval = None
        self._last_datagram_sent = None
        self._send_buff = ""
        self._times_retried = 0
        self._bytes_sent = 0
        self._bytes_received = 0
        self._closing = False
        logging.info(
            "%s: Initialized" % self
        )
        if self._connection_state == RUDPConnection._INIT_INITIATOR:
            self._close_user = self._close_user_addr, self._close_user_port = initiator
            self._remote_user = self._remote_user_addr, self._remote_user_port = endpoint

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


    def receive_data(self, d):
        self._bytes_received += len(d[RUDPConnection._DATA])
        self._data_socket.queue_buffer(d[RUDPConnection._DATA])

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

    def receive_kpalive(self, d):
        pass

    _RECV_FUNCS = {
        _FLAG_INIT: receive_init,
        _FLAG_CLOSE: receive_close,
        _FLAG_DATA: receive_data,
        _FLAG_ACK: receive_ack,
        _FLAG_KPALIVE: receive_kpalive,
    }

    def queue_close(self):
        self.queue_datagram(
            RUDPConnection._FLAG_CLOSE,
            self._sequence_num,
            "",
        )

    def init_close(self, queue_close=True):
        self._closing = True
        if self._data_socket and not self._data_socket._closing:
            self._data_socket.init_close()
        self._data_socket = None
        if queue_close:
            self.queue_close()
        self._rudp_manager.close_connection(self)

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
            if d[RUDPConnection._FLAG] == RUDPConnection._FLAG_INIT:
                    self.queue_ack()

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

    def queue_buffer(self, buf):
        self._send_buff += buf
        self.queue_datagram(
            RUDPConnection._FLAG_DATA,
            self._sequence_num,
            self._send_buff[:constants._DATA_LENGTH],
        )
        self._send_buff = self._send_buff[constants._DATA_LENGTH:]

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


    def queue_ack(self):
        self.queue_datagram(
            RUDPConnection._FLAG_ACK,
            self._peer_sequence_num,
            ""
        )

    def queue_kp_alive(self):
        self.queue_datagram(
            RUDPConnection._FLAG_KPALIVE,
            self._sequence_num,
            ""
        )

    def retry_send(self):
        datagram, params = self._last_datagram_sent
        self.queue_datagram(
            flag=params[RUDPConnection._FLAG],
            sqn_num=params[RUDPConnection._SQN_NUM],
            data=params[RUDPConnection._DATA],
            retry=True,
        )

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

    def __repr__(self):
        return "Connection (%s, %s), %s" % (self._rudp_peer_addr, self._rudp_peer_port, self._cid)
