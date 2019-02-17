import unittest

from pyeventsystem.events import SimpleEventDispatcher
from pyeventsystem.middleware import SimpleMiddlewareManager
from pyeventsystem.middleware import implement

from cloudbridge.cloud.base.middleware import EventDebugLoggingMiddleware
from cloudbridge.cloud.base.middleware import ExceptionWrappingMiddleware
from cloudbridge.cloud.interfaces.exceptions import CloudBridgeBaseException
from cloudbridge.cloud.interfaces.exceptions import \
    InvalidConfigurationException

from .helpers import skipIfPython


class ExceptionWrappingMiddlewareTestCase(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_unknown_exception_is_wrapped(self):
        EVENT_NAME = "an.exceptional.event"

        class SomeDummyClass(object):

            @implement(event_pattern=EVENT_NAME, priority=2500)
            def raise_a_non_cloudbridge_exception(self, *args, **kwargs):
                raise Exception("Some unhandled exception")

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = ExceptionWrappingMiddleware()
        manager.add(middleware)

        # no exception should be raised when there's no next handler
        dispatcher.dispatch(self, EVENT_NAME)

        some_obj = SomeDummyClass()
        manager.add(some_obj)

        with self.assertRaises(CloudBridgeBaseException):
            dispatcher.dispatch(self, EVENT_NAME)

    def test_cloudbridge_exception_is_passed_through(self):
        EVENT_NAME = "an.exceptional.event"

        class SomeDummyClass(object):

            @implement(event_pattern=EVENT_NAME, priority=2500)
            def raise_a_cloudbridge_exception(self, *args, **kwargs):
                raise InvalidConfigurationException()

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        some_obj = SomeDummyClass()
        manager.add(some_obj)
        middleware = ExceptionWrappingMiddleware()
        manager.add(middleware)

        with self.assertRaises(InvalidConfigurationException):
            dispatcher.dispatch(self, EVENT_NAME)


class EventDebugLoggingMiddlewareTestCase(unittest.TestCase):

    _multiprocess_can_split_ = True

    # Only python 3 has assertLogs support
    @skipIfPython("<", 3, 0)
    def test_messages_logged(self):
        EVENT_NAME = "an.exceptional.event"

        class SomeDummyClass(object):

            @implement(event_pattern=EVENT_NAME, priority=2500)
            def return_some_value(self, *args, **kwargs):
                return "hello world"

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = EventDebugLoggingMiddleware()
        manager.add(middleware)
        some_obj = SomeDummyClass()
        manager.add(some_obj)

        with self.assertLogs('cloudbridge.cloud.base.middleware',
                             level='DEBUG') as cm:
            dispatcher.dispatch(self, EVENT_NAME,
                                "named_param", keyword_param="hello")
        self.assertTrue(
            "named_param" in cm.output[0]
            and "keyword_param" in cm.output[0] and "hello" in cm.output[0],
            "Log output {0} not as expected".format(cm.output[0]))
        self.assertTrue(
            "hello world" in cm.output[1],
            "Log output {0} does not contain result".format(cm.output[1]))
