import inspect
import logging
import sys

import six

from ..base.events import ImplementingEventHandler
from ..base.events import InterceptingEventHandler
from ..base.events import ObservingEventHandler
from ..interfaces.events import EventHandler
from ..interfaces.exceptions import CloudBridgeBaseException
from ..interfaces.middleware import Middleware
from ..interfaces.middleware import MiddlewareManager

log = logging.getLogger(__name__)


def intercept(event_pattern, priority):
    def deco(f):
        # Mark function as having an event_handler so we can discover it
        # The callback cannot be set to f as it is not bound yet and will be
        # set during auto discovery
        f.__event_handler = InterceptingEventHandler(
            event_pattern, priority, None)
        return f
    return deco


def observe(event_pattern, priority):
    def deco(f):
        # Mark function as having an event_handler so we can discover it
        # The callback cannot be set to f as it is not bound yet and will be
        # set during auto discovery
        f.__event_handler = ObservingEventHandler(
            event_pattern, priority, None)
        return f
    return deco


def implement(event_pattern, priority):
    def deco(f):
        # Mark function as having an event_handler so we can discover it
        # The callback cannot be set to f as it is not bound yet and will be
        # set during auto discovery
        f.__event_handler = ImplementingEventHandler(
            event_pattern, priority, None)
        return f
    return deco


class SimpleMiddlewareManager(MiddlewareManager):

    def __init__(self, event_manager):
        self.events = event_manager
        self.middleware_list = []

    def add(self, middleware):
        if isinstance(middleware, Middleware):
            m = middleware
        else:
            m = AutoDiscoveredMiddleware(middleware)
        m.install(self.events)
        self.middleware_list.append(m)
        return m

    def remove(self, middleware):
        middleware.uninstall()
        self.middleware_list.remove(middleware)


class BaseMiddleware(Middleware):

    def __init__(self):
        self.event_handlers = []
        self.events = None

    def install(self, event_manager):
        self.events = event_manager
        discovered_handlers = self.discover_handlers(self)
        self.add_handlers(discovered_handlers)

    def add_handlers(self, handlers):
        if not hasattr(self, "event_handlers"):
            # In case the user forgot to call super class init
            self.event_handlers = []
        for handler in handlers:
            self.events.subscribe(handler)
        self.event_handlers.extend(handlers)

    def uninstall(self):
        for handler in self.event_handlers:
            handler.unsubscribe()
        self.event_handlers = []
        self.events = None

    @staticmethod
    def discover_handlers(class_or_obj):

        # https://bugs.python.org/issue30533
        # simulating a getmembers_static to be easily replaced with the
        # function if they add it to inspect module
        def getmembers_static(obj, predicate=None):
            results = []
            for key in dir(obj):
                if not inspect.isdatadescriptor(getattr(obj.__class__,
                                                        key,
                                                        None)):
                    try:
                        value = getattr(obj, key)
                    except AttributeError:
                        continue
                    if not predicate or predicate(value):
                        results.append((key, value))
            return results

        discovered_handlers = []
        for _, func in getmembers_static(class_or_obj, inspect.ismethod):
            handler = getattr(func, "__event_handler", None)
            if handler and isinstance(handler, EventHandler):
                # Set the properly bound method as the callback
                handler.callback = func
                discovered_handlers.append(handler)
        return discovered_handlers


class AutoDiscoveredMiddleware(BaseMiddleware):

    def __init__(self, class_or_obj):
        super(AutoDiscoveredMiddleware, self).__init__()
        self.obj_to_discover = class_or_obj

    def install(self, event_manager):
        super(AutoDiscoveredMiddleware, self).install(event_manager)
        discovered_handlers = self.discover_handlers(self.obj_to_discover)
        self.add_handlers(discovered_handlers)


class EventDebugLoggingMiddleware(BaseMiddleware):
    """
    Logs all event parameters. This middleware should not be enabled other
    than for debugging, as it could log sensitive parameters such as
    access keys.
    """
    def setup(self):
        self.add_observer(
            event_pattern="*", priority=1100, callback=self.pre_log_event)
        self.add_interceptor(
            event_pattern="*", priority=1150, callback=self.post_log_event)

    @observe(event_pattern="*", priority=1100)
    def pre_log_event(self, **kwargs):
        log.debug("Event: {0} invoked with args: {1}".format(
            kwargs.get("event"), kwargs))

    @intercept(event_pattern="*", priority=1150)
    def post_log_event(self, **kwargs):
        next_handler = kwargs.pop("next_handler")
        result = next_handler.invoke(**kwargs)
        log.debug("Event: {0} result: {1}".format(
            kwargs.get("event"), result))
        return result


class ExceptionWrappingMiddleware(BaseMiddleware):
    """
    Wraps all unhandled exceptions in cloudbridge exceptions.
    """
    def setup(self):
        self.add_interceptor(
            event_pattern="*", priority=1050, callback=self.wrap_exception)

    def wrap_exception(self, **kwargs):
        next_handler = kwargs.pop("next_handler")
        try:
            return next_handler.invoke(**kwargs)
        except Exception as e:
            if isinstance(e, CloudBridgeBaseException):
                raise
            else:
                ex_type, ex_value, traceback = sys.exc_info()
                cb_ex = CloudBridgeBaseException(
                    "CloudBridgeBaseException: {0} from exception type: {1}"
                    .format(ex_value, ex_type))
                if sys.version_info >= (3, 0):
                    six.raise_from(cb_ex, e)
                else:
                    six.reraise(CloudBridgeBaseException, cb_ex, traceback)
