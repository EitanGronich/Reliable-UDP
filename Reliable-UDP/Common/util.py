#!/usr/bin/python

## @package Reliable-UDP.Common.util
## @file util.py Implementation of @ref Reliable-UDP.Common.util

from datetime import datetime
import os
import socket
import errno
import constants
import logging
import signal

##Checks if tcp address if proper.
# @param address (tuple) TCP address
# @returns (bool) True or None
def check_tcp_address(address):
    addr, port = address
    try:
        socket.inet_aton(addr)
    except:
        return None
    if port < constants._MIN_PORT or port > constants._MAX_PORT:
        return None
    return True

## Inits log to file and file-level
# @param log (string) log filename
# @param log_level (int) log level numerical value
def init_log(log, log_level):
    logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s', level=log_level, filename=log)

##Checks if TCP port is proper.
# @param port (int) port
# @returns (bool) Boolean or None
def check_tcp_port(port):
    if port < constants._MIN_PORT or port > constants._MAX_PORT:
        return None
    return True

##Tries to convert string to int, if successful returns
# the int, otherwise None.
# @param i (string) string to convert
# @returns (bool) True or None
def str_to_int(i):
    try:
        i = int(i)
    except ValueError:
        return None
    return i

##Tries to convert string to float, if successful returns
# the float, otherwise None.
# @param f (string) string to convert
# @returns (bool) True or None
def str_to_float(f):
    try:
        f = float(f)
    except ValueError:
        return None
    return f

##Sends the whole given buffer in TCP protocol.
# @param s (string) socket
# @param buff (string) buff
def send_all(s, buff):
    while buff:
        buff = buff[s.send(buff):]

##Returns present datetime in nice format.
# @param now (datetime) datetime
# @returns (string) nice format
def present_datetime(now):
    return "%s.%s.%s, %02d:%02d:%02d:%03d" % (
        now.day,
        now.month,
        now.year,
        now.hour,
        now.minute,
        now.second,
        now.microsecond / 1000,
    )

##Smart split, if sep exists splits on first occurrence,
#otherwise return None and whole buffer.
# @param buffer (string) buffer
# @param sep (string) seperator
# @returns (tuple) split buffer or None + whole buffer.
def split_buffer(buffer, sep):
    i = buffer.find(sep)
    if i == -1:
        return (None, buffer)
    else:
        return (buffer[:i], buffer[(i+len(sep)):])

##Turns program into a daemon.
def daemon():
    import resource
    child = os.fork()
    if child != 0:
        os._exit(0)
    for i in range(
        constants._STD_ERR + 1,
        resource.getrlimit(
            resource.RLIMIT_NOFILE
        )[1]
    ):
        try:
            os.close(i)
        except OSError as e:
            if e.errno != errno.EBADF:
                raise
    fd = os.open(os.devnull, os.O_RDWR, 0o666)
    for i in (constants._STD_IN, constants._STD_OUT, constants._STD_ERR):
        os.dup2(
            i,
            fd
        )
    os.close(fd)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
