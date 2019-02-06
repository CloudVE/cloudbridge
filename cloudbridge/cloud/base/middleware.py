import logging
from abc import abstractmethod


from ..interfaces.middleware import Middleware
from ..interfaces.middleware import MiddlewareManager

log = logging.getLogger(__name__)


class SimpleMiddlewareManager(MiddlewareManager):

    def __init__(self, event_manager):
        self.events = event_manager
        self.middleware = []

    def add(self, middleware):
        self.middleware.append(middleware)
        middleware.install(self.events)

    def remove(self, middleware):
        middleware.uninstall()
        self.middleware.remove(middleware)


class BaseMiddleware(Middleware):

    def install(self, event_manager):
        self.event_handlers = []
        self.events = event_manager
        self.setup()

    @abstractmethod
    def setup(self):
        pass

    def add_observer(self, event_pattern, priority, callback):
        handler = self.events.observe(event_pattern, priority, callback)
        self.event_handlers.append(handler)

    def add_interceptor(self, event_pattern, priority, callback):
        handler = self.events.intercept(event_pattern, priority, callback)
        self.event_handlers.append(handler)

    def uninstall(self):
        for handler in self.event_handlers:
            handler.unsubscribe()
        self.events = None
