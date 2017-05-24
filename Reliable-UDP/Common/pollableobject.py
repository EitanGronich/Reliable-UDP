#!/usr/bin/python

import asyncio
import logging

class PollableObject(object):

    """
        Generic class of pollable objects.
        Such an object includes a fileno for polling,
        a logging fd, a timeout for polling, and an
        async manager object.
    """

    def __init__(
        self,
        async_manager,
        fileno,
        timeout,
    ):
        self._fileno = fileno
        self._timeout = timeout
        self._closing = False
        self._async_manager = async_manager
        self._async_manager.register(self)
        logging.info("%s: Initialized" % self)

    def update(self):
        if self._closing:
            self.terminate()

    def receive_event(self, event):
        if event & asyncio.BaseEvent.POLLIN:
            self.read()
        if event & asyncio.BaseEvent.POLLOUT:
            self.write()
        if event & asyncio.BaseEvent.POLLERR:
            self.log_error()
            self.terminate()

    def get_sleep_time(self):
        return self._timeout

    def init_close(self):
        self._closing = True

    def terminate(self):
        self._closing = True
        logging.info(
            "%s: Terminated" % self
        )
        self._async_manager.deregister(self._fileno)

    def log_error(self):
        logging.error(
            "%s: Pollerr received, closing pollable" % self
        )

    def read(self):
        pass

    def write(self):
        pass

    def get_io_mask(self):
        pass

    def __repr__(self):
        return "Pollable Object"

    @property
    def fileno(self):
        return self._fileno

    @property
    def async_manager(self):
        return self._async_manager

    @property
    def timeout(self):
        return self._timeout

    @property
    def closing(self):
        return self._closing
