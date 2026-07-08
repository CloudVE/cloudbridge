import unittest

from cloudbridge.base import helpers as cb_helpers


class BaseHelpersTestCase(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_cleanup_action_body_has_no_exception(self):
        invoke_order = [""]

        def cleanup_func():
            invoke_order[0] += "cleanup"

        with cb_helpers.cleanup_action(lambda: cleanup_func()):
            invoke_order[0] += "body_"
        self.assertEqual(invoke_order[0], "body_cleanup")

    def test_cleanup_action_body_has_exception(self):
        invoke_order = [""]

        def cleanup_func():
            invoke_order[0] += "cleanup"

        class CustomException(Exception):
            pass

        with self.assertRaises(CustomException):
            with cb_helpers.cleanup_action(lambda: cleanup_func()):
                invoke_order[0] += "body_"
                raise CustomException()
        self.assertEqual(invoke_order[0], "body_cleanup")

    def test_cleanup_action_cleanup_has_exception(self):
        invoke_order = [""]

        def cleanup_func():
            invoke_order[0] += "cleanup"
            raise Exception("test")

        with cb_helpers.cleanup_action(lambda: cleanup_func()):
            invoke_order[0] += "body_"
        self.assertEqual(invoke_order[0], "body_cleanup")

    def test_cleanup_action_body_and_cleanup_has_exception(self):
        invoke_order = [""]

        def cleanup_func():
            invoke_order[0] += "cleanup"
            raise Exception("test")

        class CustomException(Exception):
            pass

        with self.assertRaises(CustomException):
            with cb_helpers.cleanup_action(lambda: cleanup_func()):
                invoke_order[0] += "body_"
                raise CustomException()
        self.assertEqual(invoke_order[0], "body_cleanup")
