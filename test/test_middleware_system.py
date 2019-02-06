import unittest

from cloudbridge.cloud.base.events import SimpleEventDispatcher
from cloudbridge.cloud.base.middleware import BaseMiddleware
from cloudbridge.cloud.base.middleware import SimpleMiddlewareManager
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

            def setup(self):
                self.add_observer(event_pattern="some.event.*", priority=1000,
                                  callback=self.my_callback_obs)
                self.add_interceptor(event_pattern="some.*", priority=900,
                                     callback=self.my_callback_intcpt)

            def my_callback_obs(self, **kwargs):
                self.invocation_order += "observe"

            def my_callback_intcpt(self, **kwargs):
                self.invocation_order += "intercept_"
                return kwargs.get('next_handler').invoke(**kwargs)

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware = DummyMiddleWare()
        manager.add(middleware)
        dispatcher.emit(self, EVENT_NAME)

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

            def __init__(self):
                self.invocation_order = ""

            def setup(self):
                self.add_observer(event_pattern="some.really.*", priority=1000,
                                  callback=self.my_callback_obs1)
                self.add_interceptor(event_pattern="some.*", priority=900,
                                     callback=self.my_callback_intcpt2)

            def my_callback_obs1(self, **kwargs):
                self.invocation_order += "observe"

            def my_callback_intcpt2(self, **kwargs):
                self.invocation_order += "intercept_"
                return kwargs.get('next_handler').invoke(**kwargs)

        class DummyMiddleWare2(BaseMiddleware):

            def __init__(self):
                self.invocation_order = ""

            def setup(self):
                self.add_observer(event_pattern="some.really.*", priority=1050,
                                  callback=self.my_callback_obs1)
                self.add_interceptor(event_pattern="*", priority=950,
                                     callback=self.my_callback_intcpt2)

            def my_callback_obs1(self, **kwargs):
                self.invocation_order += "observe"

            def my_callback_intcpt2(self, **kwargs):
                self.invocation_order += "intercept_"
                return kwargs.get('next_handler').invoke(**kwargs)

        dispatcher = SimpleEventDispatcher()
        manager = SimpleMiddlewareManager(dispatcher)
        middleware1 = DummyMiddleWare1()
        middleware2 = DummyMiddleWare2()
        manager.add(middleware1)
        manager.add(middleware2)
        dispatcher.emit(self, EVENT_NAME)

        # Callbacks in both middleware classes should be registered
        self.assertListEqual(
            [middleware1.my_callback_intcpt2, middleware2.my_callback_intcpt2,
             middleware1.my_callback_obs1, middleware2.my_callback_obs1],
            [handler.callback for handler
             in dispatcher.get_handlers_for_event(EVENT_NAME)])

        manager.remove(middleware1)

        # Only middleware2 callbacks should be registered
        self.assertListEqual(
            [middleware2.my_callback_intcpt2, middleware2.my_callback_obs1],
            [handler.callback for handler in
             dispatcher.get_handlers_for_event(EVENT_NAME)])
