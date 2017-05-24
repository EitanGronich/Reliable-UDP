import argparse
from ...Common import constants, util, asyncio
from filesendersocket import FileSenderSocket
from openlisteningportsocket import OpenListeningPortSocket
import signal
import logging

def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--connect-address',
        help="Address of server that program connects to to ask for listening sockets",
        #required=True,
        default="127.0.0.1",
    )
    parser.add_argument(
        '--connect-port',
        type=int,
        help="Control port of server that program connects to to ask for listening sockets",
        #required=True,
        default=1025,
    )
    parser.add_argument(
        '--listening-ports',
        type=int,
        help="Number of listening ports to ask for",
        required=True,
    )
    parser.add_argument(
        '--connections-per-port',
        type=int,
        help="Number of times to connect to each listening port",
        required=True,
    )
    parser.add_argument(
        '--block-size',
        type=int,
        help="Size of reading block",
        default=1024,
    )
    parser.add_argument(
        '--send-file',
        help="File to send",
        #required=True,
        default="send_file.txt",
    )
    parser.add_argument(
        '--exit-address',
        help="RUDP Server to exit through",
        #required=True,
        default="127.0.0.1",
    )
    parser.add_argument(
        '--exit-port',
        type=int,
        help="RUDP Port to go through",
        #required=True,
        default=1027,
    )
    parser.add_argument(
        '--dest-address',
        help="Destination address",
        #required=True,
        default="127.0.0.1",
    )
    parser.add_argument(
        '--dest-port',
        type=int,
        help="Destination port",
        #required=True,
        default=9000,
    )
    parser.add_argument(
        '--log',
        help="Log filename"
    )
    parser.add_argument(
        '--log-level',
        help="Minimum log level - debug, info, error, critical",
        default="info",
        choices=constants._LOGGING_MAP.keys()
    )
    parser.add_argument(
        '--sleep-time',
        type=int,
        help="Sleep time in seconds of father process",
        default=1,
    )
    parser.add_argument(
        '--poller-type',
        default=asyncio.default_poller_type(),
        choices=tuple(asyncio.MAP.keys()),
    )
    args = parser.parse_args()
    args.poller_class = asyncio.MAP[args.poller_type]
    args.log_level = constants._LOGGING_MAP[args.log_level]
    return args

def connect_to_listening_sockets(s, number_of_connections, filename):
    for i in range(number_of_connections):
        FileSenderSocket(
            async_manager=s._async_manager,
            timeout=s._timeout,
            block_size=s._block_size,
            buff_limit=s._buff_limit,
            file_to_send=filename,
            connect_address=(s._s.getsockname()[0], s._port),
        )

def main():
    args = parse_args()
    util.init_log(args.log, args.log_level)

    try:
        async_manager = asyncio.AsyncIO(
            type=args.poller_class,
            timeout=constants._TIMEOUT,
        )
        for i in range(args.listening_ports):
            OpenListeningPortSocket(
                async_manager=async_manager,
                timeout=constants._TIMEOUT,
                block_size=args.block_size,
                buff_limit=constants._DATA_BUFF_LIMIT,
                listening_port_data={
                    "exit_address": args.exit_address,
                    "exit_port": args.exit_port,
                    "dest_address": args.dest_address,
                    "dest_port": args.dest_port,
                },
                action=connect_to_listening_sockets,
                args=[args.connections_per_port, args.send_file],
                connect_address=(args.connect_address, args.connect_port),
            )
        def handler_exit(signalnum, frame):
            logging.info("Closing sender program...")
            async_manager.init_close()
        signal.signal(signal.SIGINT, handler_exit)
        async_manager.run()
    finally:
        logging.info("Sender program terminated")

if __name__ == "__main__":
    main()
