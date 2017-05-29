#!/usr/bin/python

## @package Reliable-UDP.Common.asyncio AsyncIO module.
## @file base.py Implementation of @ref Reliable-UDP.asyncio

import errno
import os
import select
import traceback
import logging

## Base I/O event.
#
class BaseEvent(object):
    if os.name != "nt":
        ##POLLIN/POLLOUT/POLLER values in case of POSIX.
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
        ##POLLIN/POLLOUT/POLLER values in case of Windows.
        (
            POLLIN,
            POLLOUT,
            POLLERR,
        ) = (
            1,
            4,
            8,
        )

    ##Init function of BaseEvent class.
    # @returns (BaseEvent) BaseEvent object
    def __init__(self):
        pass

    ##Register function of BaseEvent class.
    def register(self):
        pass

    ##Poll function of BaseEvent class.
    def poll(self):
        pass

from tcpserver import DisconnectError

## Poll event.
#
class PollEvent(BaseEvent):

    ##Name of class
    NAME = "poll"

    ##Init function of PollEvent.
    # @returns (PollEvent) PollEvent object
    def __init__(self):
        ##Poller object that has built-in registration
        self._poller = select.poll()

    ##Register function of PollEvent.
    # Registers a file descriptor to the poller with a mask.
    # @ param fd (int) fd to register
    # @ param mask (int) mask to register with
    def register(self, fd, mask):
        self._poller.register(fd, mask)

    ##Poll function.
    # Calls system call poll and returns the output.
    # @param timeout (int) timeout for poll system call in milliseconds
    # @returns (list) list of 2-length tuples: fd and event.
    def poll(self, timeout):
        return self._poller.poll(timeout)

## Select event.
#
class SelectEvent(BaseEvent):
    NAME = "select"

    ##Init function of SelectEvent.
    # @returns (SelectEvent) SelectEvent object
    def __init__(self):
        ##Dictionary of file descriptors to IO masks.
        self._fds = {}

    ##Register function of SelectEvent.
    # Registers a file descriptor to the poller with a mask.
    # @ param fd (int) fd to register
    # @ param mask (int) mask to register with
    def register(self, fd, mask):
        self._fds[fd] = mask

    ##Poll function.
    # Implements poll with select.
    # Calls system call select and returns the output as poll output
    # @param timeout (int) timeout for select system call in milliseconds
    # @returns (list) list of 2-length tuples: fd and event.
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

##Map of class name to class for each event type
MAP = {
    e.NAME: e for e in BaseEvent.__subclasses__()
}

##Decides default poller type based on OS
# @returns (string) poller type
def default_poller_type():
    if os.name == "nt":
        return 'select'
    else:
        return 'poll'

## Poller object.
#
# Holds fds and their according object and polls them.
#
class Poller(object):

    ##Init function for Async manager (poller)
    # @param type (Class) poller type
    # @param timeout (int) default timeout of poller in milliseconds
    # @returns (Poller) Poller object
    def __init__(
        self,
        type,
        timeout,
    ):
        ##Type of poller - poll/select
        self._type = type
        ##Dictionary of file descriptors to matching objects
        self._pollables = {}
        ##Poll/Select default timeout
        self._timeout = timeout

    ##Register a pollable object with an fd to the poller object.
    # @param pollable (PollableObject) Pollable Object
    def register(self, pollable):
        self._pollables[pollable.fileno] = pollable

    ##Main loop of program. Builds poller, updates
    #pollables, calls on them for events etc.
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

    ##Init a poller of the matching class
    # @returns (BaseEvent) PollEvent or SelectEvent
    def init_poller(self):
        poller = self._type()
        for fd, pollable in self._pollables.items():
            poller.register(fd, pollable.get_io_mask())
        return poller

    ##Updates every pollable in the record
    def update(self):
        for fd, pollable in self._pollables.items()[:]:
            pollable.update()

    ##Starts clean close, moves every pollable to closing state.
    def init_close(self):
        for pollable in self._pollables.values()[:]:
            pollable.init_close()

    ##Terinates completely, deletes every pollable.
    def terminate(self):
        for pollable in self._pollables.values()[:]:
            pollable.terminate()

    ##Deregisters a pollable from the poller object, by
    #file descriptor.
    # @param fd (int) file descriptor of pollable to deregister
    def deregister(self, fd):
        del self._pollables[fd]

    ##Calculates sleep time of next poll() call by
    #calculating minimum of all sleep times wanted by pollables.
    # @ returns (int) timeout in milliseconds
    def get_min_sleep_time(self):
        if self._pollables:
            return min(
                [
                    pollable.get_sleep_time() for pollable in self._pollables.values()
                ]
            )
        else:
            return self._timeout
