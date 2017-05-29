#!/usr/bin/python

## @package Reliable-UDP.Server.__main__
## @file __main__.py Implementation of @ref Reliable-UDP.Server.__main__

import logging
import argparse
from rudpmanager import RUDPManager
import signal
from ..Common import util, constants, asyncio
from controlserver import ControlListener
from httpserver import HTTPListener


##Program argument parsing.
# @returns (argparse.Namespace) program arguments
def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--rudp-port',
        type=int,
        default=constants._RUDP_PORT,
        help="RUDP Protocol port"
    )
    parser.add_argument(
        '--control-port',
        type=int,
        default=constants._CONTROL_PORT,
        help="Control Socket Port"
    )
    parser.add_argument(
        '--http-port',
        type=int,
        default=constants._HTTP_PORT,
        help="HTTP Protocol Port"
    )
    parser.add_argument(
        '--random-drop',
        type=int,
        default=0,
        help="Percentage chance that a given packet will be dropped in RUDP protocol (testing)"
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
        '--daemon',
        help="Turn server into daemon process",
        action='store_true',
        default=False,
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

##Program main
def __main__():
    args = parse_args()
    if args.daemon:
        util.daemon()
    util.init_log(args.log, args.log_level)

    try:
        async_manager = asyncio.Poller(
            type=args.poller_class,
            timeout=constants._TIMEOUT,
        )
        rudp_manager = RUDPManager(
            async_manager=async_manager,
            bind_address=("0.0.0.0", args.rudp_port),
            timeout=constants._TIMEOUT,
            random_drop=args.random_drop,
        )
        ControlListener(
            async_manager=async_manager,
            rudp_manager=rudp_manager,
            bind_address=("0.0.0.0", args.control_port),
            timeout=constants._TIMEOUT,
            block_size=constants._CONTROL_BLOCK_SIZE,
            buff_limit=constants._CONTROL_BUFF_LIMIT,
        )
        HTTPListener(
            async_manager=async_manager,
            rudp_manager=rudp_manager,
            bind_address=("0.0.0.0", args.http_port),
            timeout=constants._TIMEOUT,
            block_size=constants._HTTP_BLOCK_SIZE,
            buff_limit=constants._HTTP_BUFF_LIMIT,
        )
        def handler_exit(signalnum, frame):
            logging.info("Closing RUDP server...")
            async_manager.init_close()
        signal.signal(signal.SIGINT, handler_exit)
        async_manager.run()
    finally:
        logging.info("RUDP Server Terminated")

if __name__ == "__main__":
        __main__()
