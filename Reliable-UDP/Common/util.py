#!/usr/bin/python

from datetime import datetime
import os
import socket
import errno
import constants
import logging

def check_tcp_address(address):
    addr, port = address
    try:
        socket.inet_aton(addr)
    except:
        return None
    if port < constants._MIN_PORT or port > constants._MAX_PORT:
        return None
    return True

def init_log(log, log_level):
    logging.basicConfig(format='%(levelname)s:%(asctime)s:%(message)s', level=log_level)
    if log is not None:
        try:
            os.remove(log)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
        logging.basicConfig(filename=log)

def check_tcp_port(port):
    if port < constants._MIN_PORT or port > constants._MAX_PORT:
        return None
    return True

def str_to_int(i):
    try:
        i = int(i)
    except ValueError:
        return None
    return i

def str_to_float(f):
    try:
        f = float(f)
    except ValueError:
        return None
    return f

def send_all(s, buff):
    while buff:
        buff = buff[s.send(buff):]

def log(fd, data):
    os.write(
        fd,
        (
            "[%s]\n"
            "%s\n"
            "\n"
        ) % (
            present_datetime(datetime.now()),
            data,
        )
    )

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

def split_buffer(buffer, sep):
    i = buffer.find(sep)
    if i == -1:
        return (None, buffer)
    else:
        return (buffer[:i], buffer[(i+len(sep)):])
