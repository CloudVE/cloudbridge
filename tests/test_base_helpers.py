import unittest

from cloudbridge.base import helpers as cb_helpers
from cloudbridge.interfaces.exceptions import InvalidParamException


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

    def test_deprecated_alias_no_rename(self):
        param_values = {}

        @cb_helpers.deprecated_alias(old_param='new_param')
        def custom_func(new_param=None, old_param=None):
            param_values['new_param'] = new_param
            param_values['old_param'] = old_param

        custom_func(new_param="hello")
        self.assertDictEqual(param_values,
                             {
                                 'new_param': "hello",
                                 'old_param': None
                             })

    def test_deprecated_alias_force_rename(self):
        param_values = {}

        @cb_helpers.deprecated_alias(old_param='new_param')
        def custom_func(new_param=None, old_param=None):
            param_values['new_param'] = new_param
            param_values['old_param'] = old_param

        custom_func(old_param="hello")
        self.assertDictEqual(param_values,
                             {
                                 'new_param': "hello",
                                 'old_param': None
                             })

    def test_deprecated_alias_force_conflict(self):
        param_values = {}

        @cb_helpers.deprecated_alias(old_param='new_param')
        def custom_func(new_param=None, old_param=None):
            param_values['new_param'] = new_param
            param_values['old_param'] = old_param

        with self.assertRaises(InvalidParamException):
            custom_func(new_param="world", old_param="hello")
