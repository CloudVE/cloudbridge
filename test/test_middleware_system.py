import unittest

from cloudbridge.cloud.base.events import SimpleEventDispatcher
from cloudbridge.cloud.base.middleware import BaseMiddleware
from cloudbridge.cloud.base.middleware import SimpleMiddlewareManager
from cloudbridge.cloud.base.middleware import intercept
from cloudbridge.cloud.base.middleware import observe
from cloudbridge.cloud.interfaces.middleware import Middleware


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

            @observe(event_pattern="some.event.*", priority=1000)
            def my_callback_obs(self, *args, **kwargs):
                self.invocation_order += "observe"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"

            @intercept(event_pattern="some.event.*", priority=900)
            def my_callback_intcpt(self, event_args, *args, **kwargs):
                self.invocation_order += "intercept_"
                assert 'first_pos_arg' in args
                assert kwargs.get('a_keyword_arg') == "something"
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = DummyMiddleWare()
        manager.add(middleware)
        dispatcher.emit(self, EVENT_NAME, 'first_pos_arg',
                        a_keyword_arg='something')

        self.assertEqual(middleware.invocation_order, "intercept_observe")
        self.assertListEqual(
            [middleware.my_callback_intcpt, middleware.my_callback_obs],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware)

        self.assertListEqual([], dispatcher.get_handlers_for_event(EVENT_NAME))

    def test_multiple_middleware(self):
        EVENT_NAME = "some.really.interesting.event.occurred"

        class DummyMiddleWare1(BaseMiddleware):

            @observe(event_pattern="some.really.*", priority=1000)
            def my_callback_obs1(self, *args, **kwargs):
                pass

            @intercept(event_pattern="some.*", priority=900)
            def my_callback_intcpt2(self, event_args, *args, **kwargs):
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

        class DummyMiddleWare2(BaseMiddleware):

            @observe(event_pattern="some.really.*", priority=1050)
            def my_callback_obs3(self, *args, **kwargs):
                pass

            @intercept(event_pattern="*", priority=950)
            def my_callback_intcpt4(self, event_args, *args, **kwargs):
                next_handler = event_args.get('next_handler')
                return next_handler.invoke(event_args, *args, **kwargs)

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware1 = DummyMiddleWare1()
        middleware2 = DummyMiddleWare2()
        manager.add(middleware1)
        manager.add(middleware2)
        dispatcher.emit(self, EVENT_NAME)

        # Callbacks in both middleware classes should be registered
        self.assertListEqual(
            [middleware1.my_callback_intcpt2, middleware2.my_callback_intcpt4,
             middleware1.my_callback_obs1, middleware2.my_callback_obs3],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware1)

        # Only middleware2 callbacks should be registered
        self.assertListEqual(
            [middleware2.my_callback_intcpt4, middleware2.my_callback_obs3],
            [handler.callback for handler in
             dispatcher.get_handlers_for_event(EVENT_NAME)])

        # add middleware back to check that internal state is properly handled
        manager.add(middleware1)

        # should one again equal original list
        self.assertListEqual(
            [middleware1.my_callback_intcpt2, middleware2.my_callback_intcpt4,
             middleware1.my_callback_obs1, middleware2.my_callback_obs3],
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

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        some_obj = SomeDummyClass()
        middleware = manager.add(some_obj)
        dispatcher.emit(self, EVENT_NAME)

        # Middleware should be discovered even if class containing interceptors
        # doesn't inherit from Middleware
        self.assertListEqual(
            [some_obj.my_callback_intcpt2, some_obj.my_callback_obs1],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware)

        # Callbacks should be correctly removed
        self.assertListEqual(
            [],
            [handler.callback for handler in
             dispatcher.get_handlers_for_event(EVENT_NAME)])
