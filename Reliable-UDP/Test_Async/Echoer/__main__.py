#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Test_Async.Echoer.__main__
## @file __main__.py Implementation of @ref  Reliable-UDP.Reliable-UDP.Test_Async.Echoer.__main__


from ...Common import asyncio, util, constants
import argparse
from echoserver import EchoListener
import signal
import logging

def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bind-port',
        type=int,
        help="Port that accepts connections",
        required=True,
    )
    parser.add_argument(
        '--block-size',
        type=int,
        help="Size of reading block",
        default=1024,
    )
    parser.add_argument(
        '--log-level',
        help="Minimum log level - debug, info, error, critical",
        default="info",
        choices=constants._LOGGING_MAP.keys()
    )
    parser.add_argument(
        '--log',
        help="Log filename"
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

def main():
    args = parse_args()
    util.init_log(args.log, args.log_level)

    try:
        async_manager = asyncio.Poller(
            type=args.poller_class,
            timeout=constants._TIMEOUT,
        )
        EchoListener(
            bind_address=("0.0.0.0", args.bind_port),
            async_manager=async_manager,
            timeout=constants._TIMEOUT,
            block_size=args.block_size,
            buff_limit=constants._DATA_BUFF_LIMIT,
        )
        def handler_exit(signalnum, frame):
            logging.info("Closing echoer program...")
            async_manager.init_close()
        signal.signal(signal.SIGINT, handler_exit)
        async_manager.run()
    finally:
        logging.info("Echoer program terminated")

if __name__ == "__main__":
    main()
