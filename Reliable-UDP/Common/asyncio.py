#!/usr/bin/python

import errno
import os
import select
import traceback
import logging

STANDARD_INPUT = 0
STANDARD_OUTPUT = 1
STANDARD_ERROR = 2


class BaseEvent(object):
    if os.name != "nt":
        (
            POLLIN,
            POLLOUT,
            POLLERR,
        ) = (
            select.POLLIN,
            select.POLLOUT,
            select.POLLERR,
        )
    else:
        (
            POLLIN,
            POLLOUT,
            POLLERR,
        ) = (
            1,
            4,
            8,
        )

    def __init__(self):
        pass

    def register(self):
        pass

    def poll(self):
        pass

from tcpserver import DisconnectError

class PollEvent(BaseEvent):
    NAME = "poll"

    def __init__(self):
        self._poller = select.poll()

    def register(self, fd, mask):
        self._poller.register(fd, mask)

    def poll(self, timeout):
        return self._poller.poll(timeout)


class SelectEvent(BaseEvent):
    NAME = "select"

    def __init__(self):
        self._fds = {}

    def register(self, fd, mask):
        self._fds[fd] = mask

    def poll(self, timeout):
        read, write, error = [], [], []
        for fd, mask in self._fds.items():
            if mask & BaseEvent.POLLIN:
                read.append(fd)
            if mask & BaseEvent.POLLOUT:
                write.append(fd)
            error.append(fd)
        read, write, error = select.select(read, write, error, timeout / 1000.0)
        poller = []
        for fd in read:
            poller.append((fd, BaseEvent.POLLIN))
        for fd in write:
            poller.append((fd, BaseEvent.POLLOUT))
        for fd in error:
            poller.append((fd, BaseEvent.POLLERR))
        return poller

MAP = {
    e.NAME: e for e in BaseEvent.__subclasses__()
}

def default_poller_type():
    if os.name == "nt":
        return 'select'
    else:
        return 'poll'


class Poller(object):

    def __init__(
        self,
        type,
        timeout,
    ):
        self._type = type
        self._pollables = {}
        self._timeout = timeout

    def register(self, pollable):
        self._pollables[pollable.fileno] = pollable

    def run(self):
        while self._pollables:
            try:
                self.update()
                for fd, event in self.init_poller().poll(self.get_min_sleep_time()):
                    try:
                        try:
                            self._pollables[fd].receive_event(event)
                        except IOError as e:
                            if e.errno not in (errno.EWOULDBLOCK, errno.EAGAIN):
                                raise
                        except DisconnectError:
                            self._pollables[fd].terminate()
                    except Exception as e:
                        logging.error(
                            (
                                "Unexpected error in %s, terminating %s:\n"
                                "%s\n"
                            ) % (
                                    self._pollables[fd],
                                    self._pollables[fd],
                                    traceback.format_exc(),
                            )
                        )
                        self._pollables[fd].terminate()
            except Exception as e:
                if e[0] != errno.EINTR:
                    logging.critical(
                        (
                            "Unexpected error in server, closing server:\n"
                            "%s"
                        ) % traceback.format_exc()
                    )
                    self.terminate()
                else:
                    self.init_close()

    def init_poller(self):
        poller = self._type()
        for fd, pollable in self._pollables.items():
            poller.register(fd, pollable.get_io_mask())
        return poller

    def update(self):
        for fd, pollable in self._pollables.items()[:]:
            pollable.update()

    def init_close(self):
        for pollable in self._pollables.values()[:]:
            pollable.init_close()

    def terminate(self):
        for pollable in self._pollables.values()[:]:
            pollable.terminate()

    def deregister(self, fd):
        del self._pollables[fd]

    def get_min_sleep_time(self):
        if self._pollables:
            return min(
                [
                    pollable.get_sleep_time() for pollable in self._pollables.values()
                ]
            )
        else:
            return self._timeout
