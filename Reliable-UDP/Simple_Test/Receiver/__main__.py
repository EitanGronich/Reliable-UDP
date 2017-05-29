#!/usr/bin/python

## @package Reliable-UDP.Reliable-UDP.Simple_Test.Receiver.__main__
## @file __main__.py Implementation of @ref Reliable-UDP.Reliable-UDP.Simple_Test.Receiver.__main__

import socket
import argparse
from datetime import datetime
import os
from ...Common import constants

def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--bind-port',
        type=int,
        help="Port to accept connections on to",
        required=True,
    )
    parser.add_argument(
        '--block-size',
        type=int,
        help="Size of reading block",
        default=1024,
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(("0.0.0.0", args.bind_port))
    s.listen(10)
    s1, addr = s.accept()
    END = "\n\n"
    while True:
        buf = s1.recv(args.block_size)
        if buf.find(END) != -1:
            break
    os.write(constants._STD_OUT, "%s" % datetime.now())

if __name__ == "__main__":
    main()
