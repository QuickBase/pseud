from __future__ import unicode_literals
import functools
import logging

from future.builtins import bytes
import zmq
import zope.component
import zope.interface

from .interfaces import (IClient,
                         IHeartbeatBackend,
                         IServer,
                         HEARTBEAT,
                         VERSION)

from .utils import register_heartbeat_backend

logger = logging.getLogger(__name__)


class _BaseHeartbeatBackend(object):

    def __init__(self, rpc):
        self.rpc = rpc


@register_heartbeat_backend
@zope.interface.implementer(IHeartbeatBackend)
@zope.component.adapter(IClient)
class NoOpHeartbeatBackendForClient(_BaseHeartbeatBackend):
    """
    No op Heartbeat
    """
    name = b'noop_heartbeat_backend'

    def handle_heartbeat(self, *args):
        pass

    def handle_timeout(self, *args):
        pass

    def configure(self):
        pass

    def stop(self):
        pass


@register_heartbeat_backend
@zope.interface.implementer(IHeartbeatBackend)
@zope.component.adapter(IServer)
class NoOpHeartbeatBackendForServer(_BaseHeartbeatBackend):
    """
    No op Heartbeat
    """
    name = b'noop_heartbeat_backend'

    def handle_timeout(self, *args):
        pass

    def handle_heartbeat(self, *args):
        pass

    def configure(self):
        pass

    def stop(self):
        pass


@register_heartbeat_backend
@zope.interface.implementer(IHeartbeatBackend)
@zope.component.adapter(IClient)
class TestingHeartbeatBackendForClient(_BaseHeartbeatBackend):
    name = b'testing_heartbeat_backend'

    def handle_timeout(self, user_id, routing_id):
        pass

    def handle_heartbeat(self, user_id, routing_id):
        self.rpc.send_message([routing_id, b'', VERSION,
                               b'', HEARTBEAT, b''])

    def configure(self):
        self.periodic_callback = self.rpc.create_periodic_callback(
            functools.partial(self.handle_heartbeat, b'',
                              self.rpc.peer_routing_id), .1)

    def stop(self):
        try:
            self.periodic_callback.stop()
        except AttributeError:
            self.periodic_callback.kill()


@register_heartbeat_backend
@zope.interface.implementer(IHeartbeatBackend)
@zope.component.adapter(IServer)
class TestingHeartbeatBackendForServer(_BaseHeartbeatBackend):
    name = b'testing_heartbeat_backend'
    max_time_before_dead = .2
    callback_pool = {}

    def handle_timeout(self, user_id, routing_id):
        logger.debug('Timeout detected for {!r}'.format(routing_id))
        self.monitoring_socket.send(
            'Gone {!r}'.format(bytes(user_id)).encode())

    def handle_heartbeat(self, user_id, routing_id):
        self.monitoring_socket.send(user_id)
        previous = self.callback_pool.pop(user_id, None)
        if previous is not None:
            try:
                self.rpc.io_loop.remove_timeout(previous)
            except AttributeError:
                previous.kill()
        self.callback_pool[user_id] = self.rpc.create_later_callback(
            functools.partial(self.handle_timeout, user_id, routing_id),
            self.max_time_before_dead)

    def configure(self):
        self.monitoring_socket = self.rpc.context.socket(zmq.PUB)
        self.monitoring_socket.bind(b'ipc://testing_heartbeating_backend')

    def stop(self):
        self.monitoring_socket.close(linger=0)
        for callback in self.callback_pool.values():
            try:
                self.rpc.io_loop.remove_timeout(callback)
            except AttributeError:
                callback.kill()
        self.callback_pool.clear()
