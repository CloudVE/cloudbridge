import unittest

from cloudbridge.cloud.base.events import SimpleEventDispatcher
from cloudbridge.cloud.base.middleware import BaseMiddleware
from cloudbridge.cloud.base.middleware import EventDebugLoggingMiddleware
from cloudbridge.cloud.base.middleware import ExceptionWrappingMiddleware
from cloudbridge.cloud.base.middleware import SimpleMiddlewareManager
from cloudbridge.cloud.base.middleware import dispatch_event
from cloudbridge.cloud.base.middleware import implement
from cloudbridge.cloud.base.middleware import intercept
from cloudbridge.cloud.base.middleware import observe
from cloudbridge.cloud.interfaces.exceptions import CloudBridgeBaseException
from cloudbridge.cloud.interfaces.exceptions import \
    InvalidConfigurationException
from cloudbridge.cloud.interfaces.middleware import Middleware

from .helpers import skipIfPython


class MiddlewareSystemTestCase(unittest.TestCase):

    def test_basic_middleware(self):

        class DummyMiddleWare(Middleware):

            def __init__(self):
                self.invocation_order = ""

            def install(self, event_manager):
                self.event_manager = event_manager
                self.invocation_order += "install_"

            def uninstall(self):
                self.invocation_order += "uninstall"

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = DummyMiddleWare()
        manager.add(middleware)

        self.assertEqual(middleware.invocation_order, "install_",
                         "install should be called when adding new middleware")

        manager.remove(middleware)
        self.assertEqual(middleware.invocation_order, "install_uninstall",
                         "uninstall should be called when removing middleware")

    def test_base_middleware(self):
        EVENT_NAME = "some.event.occurred"

        class DummyMiddleWare(BaseMiddleware):

            def __init__(self):
                self.invocation_order = ""

            @intercept(event_pattern="some.event.*", priority=900)
            def my_callback_intcpt(self, event_args, *args, **kwargs):
                self.invocation_order += "intcpt_"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

            @implement(event_pattern="some.event.*", priority=950)
            def my_callback_impl(self, *args, **kwargs):
                self.invocation_order += "impl_"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"
                return "hello"

            @observe(event_pattern="some.event.*", priority=1000)
            def my_callback_obs(self, event_args, *args, **kwargs):
                self.invocation_order += "obs"
                assert 'first_pos_arg' in args
                assert event_args['result'] == "hello"
                assert kwargs.get('a_keyword_arg') == "something"

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = DummyMiddleWare()
        manager.add(middleware)
        dispatcher.dispatch(self, EVENT_NAME, 'first_pos_arg',
                            a_keyword_arg='something')

        self.assertEqual(middleware.invocation_order, "intcpt_impl_obs")
        self.assertListEqual(
            [middleware.my_callback_intcpt, middleware.my_callback_impl,
             middleware.my_callback_obs],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware)

        self.assertListEqual([], dispatcher.get_handlers_for_event(EVENT_NAME))

    def test_multiple_middleware(self):
        EVENT_NAME = "some.really.interesting.event.occurred"

        class DummyMiddleWare1(BaseMiddleware):

            @observe(event_pattern="some.really.*", priority=1000)
            def my_obs1_3(self, *args, **kwargs):
                pass

            @implement(event_pattern="some.*", priority=970)
            def my_impl1_2(self, *args, **kwargs):
                return "hello"

            @intercept(event_pattern="some.*", priority=900)
            def my_intcpt1_1(self, event_args, *args, **kwargs):
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

        class DummyMiddleWare2(BaseMiddleware):

            @observe(event_pattern="some.really.*", priority=1050)
            def my_obs2_3(self, *args, **kwargs):
                pass

            @intercept(event_pattern="*", priority=950)
            def my_intcpt2_2(self, event_args, *args, **kwargs):
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

            @implement(event_pattern="some.really.*", priority=920)
            def my_impl2_1(self, *args, **kwargs):
                pass

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware1 = DummyMiddleWare1()
        middleware2 = DummyMiddleWare2()
        manager.add(middleware1)
        manager.add(middleware2)
        dispatcher.dispatch(self, EVENT_NAME)

        # Callbacks in both middleware classes should be registered
        self.assertListEqual(
            [middleware1.my_intcpt1_1, middleware2.my_impl2_1,
             middleware2.my_intcpt2_2, middleware1.my_impl1_2,
             middleware1.my_obs1_3, middleware2.my_obs2_3],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware1)

        # Only middleware2 callbacks should be registered
        self.assertListEqual(
            [middleware2.my_impl2_1, middleware2.my_intcpt2_2,
             middleware2.my_obs2_3],
            [handler.callback for handler in
             dispatcher.get_handlers_for_event(EVENT_NAME)])

        # add middleware back to check that internal state is properly handled
        manager.add(middleware1)

        # should one again equal original list
        self.assertListEqual(
            [middleware1.my_intcpt1_1, middleware2.my_impl2_1,
             middleware2.my_intcpt2_2, middleware1.my_impl1_2,
             middleware1.my_obs1_3, middleware2.my_obs2_3],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

    def test_automatic_middleware(self):
        EVENT_NAME = "another.interesting.event.occurred"

        class SomeDummyClass(object):

            @observe(event_pattern="another.really.*", priority=1000)
            def not_a_match(self, *args, **kwargs):
                pass

            @intercept(event_pattern="another.*", priority=900)
            def my_callback_intcpt2(self, *args, **kwargs):
                pass

            def not_an_event_handler(self, *args, **kwargs):
                pass

            @observe(event_pattern="another.interesting.*", priority=1000)
            def my_callback_obs1(self, *args, **kwargs):
                pass

            @implement(event_pattern="another.interesting.*", priority=1050)
            def my_callback_impl(self, *args, **kwargs):
                pass

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        some_obj = SomeDummyClass()
        middleware = manager.add(some_obj)
        dispatcher.dispatch(self, EVENT_NAME)

        # Middleware should be discovered even if class containing interceptors
        # doesn't inherit from Middleware
        self.assertListEqual(
            [some_obj.my_callback_intcpt2, some_obj.my_callback_obs1,
             some_obj.my_callback_impl],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware)

        # Callbacks should be correctly removed
        self.assertListEqual(
            [],
            [handler.callback for handler in
             dispatcher.get_handlers_for_event(EVENT_NAME)])

    def test_event_decorator(self):
        EVENT_NAME = "some.event.occurred"

        class SomeDummyClass(object):

            def __init__(self):
                self.invocation_order = ""
                self.events = SimpleEventDispatcher()

            @intercept(event_pattern="some.event.*", priority=900)
            def my_callback_intcpt(self, event_args, *args, **kwargs):
                self.invocation_order += "intcpt_"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

            @observe(event_pattern="some.event.*", priority=3000)
            def my_callback_obs(self, event_args, *args, **kwargs):
                self.invocation_order += "obs"
                assert 'first_pos_arg' in args
                assert event_args['result'] == "hello"
                assert kwargs.get('a_keyword_arg') == "something"

            @dispatch_event(EVENT_NAME)
            def my_callback_impl(self, *args, **kwargs):
                self.invocation_order += "impl_"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"
                return "hello"

        obj = SomeDummyClass()
        manager = SimpleMiddlewareManager(obj.events)
        middleware = manager.add(obj)

        # calling my_implementation should trigger all events
        result = obj.my_callback_impl(
            'first_pos_arg', a_keyword_arg='something')

        self.assertEqual(result, "hello")
        self.assertEqual(obj.invocation_order, "intcpt_impl_obs")
        callbacks = [handler.callback for handler
                     in middleware.events.get_handlers_for_event(EVENT_NAME)]

        self.assertNotIn(
            obj.my_callback_impl, callbacks,
            "The event impl callback should not be directly contained"
            " in callbacks to avoid a circular dispatch")

        self.assertEqual(
            len(set(callbacks).difference(
                set([obj.my_callback_intcpt,
                     obj.my_callback_obs]))),
            1,
            "The event impl callback should be included in the list of"
            "  callbacks indirectly")

        manager.remove(middleware)

        # calling my_implementation again should trigger a None response
        result = obj.my_callback_impl(
            'first_pos_arg', a_keyword_arg='something')

        self.assertEqual(result, None)


class ExceptionWrappingMiddlewareTestCase(unittest.TestCase):

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
