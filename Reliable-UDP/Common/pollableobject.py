#!/usr/bin/python

## @package Reliable-UDP.Common.pollableobject
## @file pollableobject.py Implementation of @ref Reliable-UDP.Common.pollableobject


import asyncio
import logging

## General pollable object
#
# Has fd, knows its poller and receives IO events.
#
class PollableObject(object):

    """
        Generic class of pollable objects.
        Such an object includes a fileno for polling,
        a logging fd, a timeout for polling, and an
        async manager object.
    """

    ##Inits a Pollable Object
    # @param async_manager (Poller) Poller object
    # @param fileno (int) fd of object
    # @param timeout (int) default timeout in milliseconds
    # @returns (PollableObject) Pollable Object
    def __init__(
        self,
        async_manager,
        fileno,
        timeout,
    ):
        ##File descriptor of pollable object
        self._fileno = fileno
        ##Default timeout of the object
        self._timeout = timeout
        ##Boolean state of the object - closing or not
        self._closing = False
        ##Async IO manager (Poller object)
        self._async_manager = async_manager
        self._async_manager.register(self)
        logging.info("%s: Initialized" % self)

    ##Updates state of pollable object
    def update(self):
        if self._closing:
            self.terminate()

    ##Receive I/O event.
    # @param event (int) event mask.
    def receive_event(self, event):
        if event & asyncio.BaseEvent.POLLIN:
            self.read()
        if event & asyncio.BaseEvent.POLLOUT:
            self.write()
        if event & asyncio.BaseEvent.POLLERR:
            self.log_error()
            self.terminate()

    ##Returns preferred sleep time of pollable object
    # @returns (int) timeout in milliseconds.
    def get_sleep_time(self):
        return self._timeout

    ##Starts clean close of pollable object.
    def init_close(self):
        self._closing = True

    ##Terminates pollable object completely,
    #including deregister from Poller object.
    def terminate(self):
        self._closing = True
        logging.info(
            "%s: Terminated" % self
        )
        self._async_manager.deregister(self._fileno)

    ##Logs Pollerr event
    def log_error(self):
        logging.error(
            "%s: Pollerr received, closing pollable" % self
        )

    ##Logic on read event
    def read(self):
        pass

    ##Logic on write event
    def write(self):
        pass

    ##Return IO mask for registration.
    def get_io_mask(self):
        pass

    ##String representation of object.
    # @returns (string) representation
    def __repr__(self):
        return "Pollable Object"

    ##Property method for fd of object.
    # @returns (int) fd of object
    @property
    def fileno(self):
        return self._fileno

    ##Property method for Poller object.
    # @returns (Poller) Poller object
    @property
    def async_manager(self):
        return self._async_manager

    ##Property method for default timeout.
    # @returns(int) default timeout.
    @property
    def timeout(self):
        return self._timeout

    ##Property method for closing boolean.
    # @returns (bool) if object is closing or not.
    @property
    def closing(self):
        return self._closing
