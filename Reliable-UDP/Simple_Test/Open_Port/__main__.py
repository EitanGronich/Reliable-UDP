#!/usr/bin/python

## @package Reliable-UDP.Simple_Test.Open_Port.__main__
## @file __main__.py Implementation of @ref Reliable-UDP.Simple_Test.Open_Port.__main__

import socket
import argparse
from ...Common import constants, util
import os

##Program argument parsing.
# @returns (argparse.Namespace) program arguments
def parse_args():
    """Parse program argument."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--server-address',
        help="Address of RUDP server",
        required=True,
    )
    parser.add_argument(
        '--server-control-port',
        type=int,
        help="Control port of server",
    )
    parser.add_argument(
        '--exit-server-address',
        help="Address of exit server of the connection",
        required=True,
    )
    parser.add_argument(
        '--exit-server-port',
        type=int,
        help="RUDP Port of exit server",
        required=True,
    )
    parser.add_argument(
        '--destination-address',
        help="Address of destination",
        required=True,
    )
    parser.add_argument(
        '--destination-port',
        type=int,
        help="TCP Port of destination",
        required=True,
    )
    parser.add_argument(
        '--preferred-port',
        type=int,
        help="Preferred port, will return this port if it exists",
    )
    parser.add_argument(
        '--block-size',
        type=int,
        help="Size of reading block",
        default=1024,
    )
    args = parser.parse_args()
    return args

##Main program function
def main():
    args = parse_args()
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    s.connect((args.server_address, args.server_control_port))
    util.send_all(
        s,
        (
            "op=connect\n"
            "exit_address=%s\n"
            "exit_port=%s\n"
            "dest_address=%s\n"
            "dest_port=%s\n"
            "ttl=0\n" % (
                args.exit_server_address,
                args.exit_server_port,
                args.destination_address,
                args.destination_port,
            )
        )
    )
    if args.preferred_port:
        util.send_all(
            s,
            (
                "if_exists=%s\n" % args.preferred_port
            )
        )
    util.send_all(
        s,
        "\n"
    )
    buf = ""
    END = "%s%s" % (constants._LF, constants._LF)
    SEP = "="
    while True:
        buf += s.recv(args.block_size)
        i = buf.find(END)
        if i != -1:
            buf = buf[:(-len(END))]
            lines = buf.split("\n")
            for line in lines:
                field, value = line.split(SEP)
                if field == "code" and int(value) != 0:
                    raise RuntimeError('Request Failed')
                if field == "port":
                    os.write(constants._STD_OUT, "%s" % value)
            break

if __name__ == "__main__":
    main()
