import unittest

from cloudbridge.cloud.base.events import SimpleEventDispatcher
from cloudbridge.cloud.interfaces.exceptions import HandlerException


class EventSystemTestCase(unittest.TestCase):

    def test_emit_event_no_handlers(self):
        dispatcher = SimpleEventDispatcher()
        result = dispatcher.emit(self, "event.hello.world")
        self.assertIsNone(result, "Result should be none as there are no"
                          "registered handlers")

    def test_emit_event_observing_handler(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME})
            callback_tracker[0] += 'obs'
            return "hello"

        dispatcher = SimpleEventDispatcher()
        dispatcher.observe(EVENT_NAME, 1000, my_callback)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "obs", "callback should have been invoked"
            "once and contain value `obs` but tracker value is {0}".format(
                callback_tracker[0]))
        self.assertIsNone(result, "Result should be none as this is an"
                          " observing handler")

    def test_emit_event_intercepting_handler(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME,
                                  'next_handler': None})
            callback_tracker[0] += "intcpt"
            return "world"

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept(EVENT_NAME, 1000, my_callback)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "intcpt", "callback should have been invoked"
            "once and contain value `intcpt` but tracker value is {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "world", "Result should be `world` as this"
                         " is an intercepting handler")

    def test_emit_event_observe_precedes_intercept(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback_obs(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME})
            callback_tracker[0] += "obs_"
            return "hello"

        def my_callback_intcpt(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME,
                                  'next_handler': None})
            callback_tracker[0] += "intcpt_"
            return "world"

        dispatcher = SimpleEventDispatcher()
        dispatcher.observe(EVENT_NAME, 1000, my_callback_obs)
        dispatcher.intercept(EVENT_NAME, 1001, my_callback_intcpt)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "obs_intcpt_", "callback was not invoked in "
            "expected order. Should have been obs_intcpt_ but is {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "world", "Result should be `world` as this"
                         " is the return value of the intercepting handler")

    def test_emit_event_observe_follows_intercept(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback_intcpt(**kwargs):
            self.assertEqual(kwargs.get('sender'), self)
            self.assertEqual(kwargs.get('next_handler').priority, 1001)
            self.assertEqual(kwargs.get('next_handler').callback.__name__,
                             "my_callback_obs")
            callback_tracker[0] += "intcpt_"
            # invoke next handler
            retval = kwargs.get('next_handler').invoke(**kwargs)
            self.assertIsNone(retval, "Return values of observable handlers"
                              " should not be propagated.")
            return "world"

        def my_callback_obs(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME})
            callback_tracker[0] += "obs_"
            return "hello"

        dispatcher = SimpleEventDispatcher()
        # register priorities out of order to test that too
        dispatcher.observe(EVENT_NAME, 1001, my_callback_obs)
        dispatcher.intercept(EVENT_NAME, 1000, my_callback_intcpt)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "intcpt_obs_", "callback was not invoked in "
            "expected order. Should have been intcpt_obs_ but is {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "world", "Result should be `world` as this"
                         " is the return value of the intercepting handler")

    def test_emit_event_intercept_follows_intercept(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback_intcpt1(**kwargs):
            self.assertEqual(kwargs.get('sender'), self)
            self.assertEqual(kwargs.get('next_handler').priority, 2020)
            self.assertEqual(kwargs.get('next_handler').callback.__name__,
                             "my_callback_intcpt2")
            callback_tracker[0] += "intcpt1_"
            # invoke next handler but ignore return value
            return "hello" + kwargs.get('next_handler').invoke(**kwargs)

        def my_callback_intcpt2(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': EVENT_NAME,
                                  'next_handler': None})
            callback_tracker[0] += "intcpt2_"
            return "world"

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept(EVENT_NAME, 2000, my_callback_intcpt1)
        dispatcher.intercept(EVENT_NAME, 2020, my_callback_intcpt2)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "intcpt1_intcpt2_", "callback was not invoked"
            " in expected order. Should have been intcpt1_intcpt2_ but is"
            " {0}".format(callback_tracker[0]))
        self.assertEqual(result, "helloworld", "Result should be `helloworld` "
                         "as this is the expected return value from the chain")

    def test_subscribe_event_duplicate_priority(self):

        def my_callback(**kwargs):
            pass

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept("event.hello.world", 1000, my_callback)
        dispatcher.intercept("event.hello.world", 1000, my_callback)
        with self.assertRaises(HandlerException):
            dispatcher.emit(self, "event.hello.world")

    def test_subscribe_event_duplicate_wildcard_priority(self):

        def my_callback(**kwargs):
            pass

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept("event.hello.world", 1000, my_callback)
        dispatcher.intercept("event.hello.*", 1000, my_callback)
        with self.assertRaises(HandlerException):
            dispatcher.emit(self, "event.hello.world")

    def test_subscribe_event_duplicate_wildcard_priority_allowed(self):
        # duplicate priorities for different wildcard namespaces allowed
        def my_callback(**kwargs):
            pass

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept("event.hello.world", 1000, my_callback)
        dispatcher.intercept("someevent.hello.*", 1000, my_callback)
        # emit should work fine in this case with no exceptions
        dispatcher.emit(self, "event.hello.world")

    def test_subscribe_multiple_events(self):
        EVENT_NAME = "event.hello.world"
        callback_tracker = ['']

        def my_callback1(**kwargs):
            self.assertDictEqual(kwargs, {'sender': self,
                                          'event_name': EVENT_NAME})
            callback_tracker[0] += "event1_"
            return "hello"

        def my_callback2(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': "event.hello.anotherworld"})
            callback_tracker[0] += "event2_"
            return "another"

        def my_callback3(**kwargs):
            self.assertDictEqual(kwargs,
                                 {'sender': self,
                                  'event_name': "event.hello.anotherworld",
                                  'next_handler': None})
            callback_tracker[0] += "event3_"
            return "world"

        dispatcher = SimpleEventDispatcher()
        dispatcher.observe(EVENT_NAME, 2000, my_callback1)
        # register to a different event with the same priority
        dispatcher.observe("event.hello.anotherworld", 2000, my_callback2)
        dispatcher.intercept("event.hello.anotherworld", 2020, my_callback3)
        result = dispatcher.emit(self, EVENT_NAME)
        self.assertEqual(
            callback_tracker[0], "event1_", "only `event.hello.world` handlers"
            " should have been  triggered but received {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, None, "Result should be `helloworld` "
                         "as this is the expected return value from the chain")

        result = dispatcher.emit(self, "event.hello.anotherworld")
        self.assertEqual(
            callback_tracker[0], "event1_event2_event3_", "only handlers for"
            "  event `event.hello.anotherworld` should have been  triggered"
            " but received {0}".format(callback_tracker[0]))
        self.assertEqual(result, "world", "Result should be `world` "
                         "as this is the expected return value from the chain")

    def test_subscribe_wildcard(self):
        callback_tracker = ['']

        def my_callback1(**kwargs):
            callback_tracker[0] += "event1_"
            return "hello" + kwargs.get('next_handler').invoke(**kwargs)

        def my_callback2(**kwargs):
            callback_tracker[0] += "event2_"
            return "some" + kwargs.get('next_handler').invoke(**kwargs)

        def my_callback3(**kwargs):
            callback_tracker[0] += "event3_"
            return "other" + kwargs.get('next_handler').invoke(**kwargs)

        def my_callback4(**kwargs):
            callback_tracker[0] += "event4_"
            return "world"

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept("event.*", 2000, my_callback1)
        # register to a different event with the same priority
        dispatcher.intercept("event.hello.*", 2010, my_callback2)
        dispatcher.intercept("event.hello.there", 2030, my_callback4)
        dispatcher.intercept("event.*.there", 2020, my_callback3)
        dispatcher.intercept("event.*.world", 2020, my_callback4)
        dispatcher.intercept("someevent.hello.there", 2030, my_callback3)
        # emit a series of events
        result = dispatcher.emit(self, "event.hello.there")

        self.assertEqual(
            callback_tracker[0], "event1_event2_event3_event4_",
            "Event handlers executed in unexpected order {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "hellosomeotherworld")

        result = dispatcher.emit(self, "event.test.hello.world")
        self.assertEqual(
            callback_tracker[0], "event1_event2_event3_event4_event1_event4_",
            "Event handlers executed in unexpected order {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "helloworld")

    # make sure cache gets invalidated when subscribing after emit
    def test_subscribe_after_emit(self):
        callback_tracker = ['']

        def my_callback1(**kwargs):
            callback_tracker[0] += "event1_"
            if kwargs.get('next_handler'):
                return "hello" + kwargs.get('next_handler').invoke(**kwargs)
            else:
                return "hello"

        def my_callback2(**kwargs):
            callback_tracker[0] += "event2_"
            return "some"

        dispatcher = SimpleEventDispatcher()
        dispatcher.intercept("event.hello.world", 1000, my_callback1)
        dispatcher.emit(self, "event.hello.world")
        dispatcher.intercept("event.hello.*", 1001, my_callback2)
        result = dispatcher.emit(self, "event.hello.world")

        self.assertEqual(
            callback_tracker[0], "event1_event1_event2_",
            "Event handlers executed in unexpected order {0}".format(
                callback_tracker[0]))
        self.assertEqual(result, "hellosome")
