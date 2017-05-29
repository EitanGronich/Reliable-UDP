#!/usr/bin/python

## @package Reliable-UDP.Simple_Test.Sender.__main__
## @file __main__.py Implementation of @ref Reliable-UDP.Simple_Test.Sender.__main__


import socket
import argparse
from datetime import datetime
import time
import os
from ...Common import constants, util

##Program argument parsing.
# @returns (argparse.Namespace) program arguments
def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--connect-address',
        help="Connect address to send the file to",
        required=True,
    )
    parser.add_argument(
        '--connect-port',
        type=int,
        help="Port to send to file to",
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
        default="send_file.txt",
    )
    args = parser.parse_args()
    return args

##Main program function
def main():
    args = parse_args()
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s.connect((args.connect_address, args.connect_port))
    fd = os.open(
        args.send_file,
        os.O_RDONLY,
        0o666,
    )
    os.write(constants._STD_OUT, "%s" % datetime.now())
    END="\n\n"
    while True:
        buf = os.read(fd, args.block_size)
        if not buf:
            break
        util.send_all(
            s,
            buf,
        )
    util.send_all(s, END)
    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
