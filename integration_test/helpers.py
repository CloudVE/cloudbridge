import functools
import os
import sys
import unittest
from contextlib import contextmanager

from six import reraise

from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import TestMockHelperMixin


def parse_bool(val):
    if val:
        return str(val).upper() in ['TRUE', 'YES']
    else:
        return False


@contextmanager
def cleanup_action(cleanup_func):
    """n csdmmnd
    Context manager to carry out a given
    cleanup action after carrying out a set
    of tasks, or when an exception occurs.
    If any errors occur during the cleanup
    action, those are ignored, and the original
    traceback is preserved.

    :params func: This function is called if
    an exception occurs or at the end of the
    context block. If any exceptions raised
        by func are ignored.
    Usage:
        with cleanup_action(lambda e: print("Oops!")):
            do_something()
    """
    try:
        yield
    except Exception:
        ex_class, ex_val, ex_traceback = sys.exc_info()
        try:
            cleanup_func()
        except Exception as e:
            print("Error during exception cleanup: {0}".format(e))
        reraise(ex_class, ex_val, ex_traceback)
    try:
        cleanup_func()
    except Exception as e:
        print("Error during cleanup: {0}".format(e))


def skipIfNoService(services):
    """
    A decorator for skipping tests if the provider
    does not implement a given service.
    """
    def wrap(func):
        """
        The actual wrapper
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            provider = getattr(self, 'provider')
            if provider:
                for service in services:
                    if not provider.has_service(service):
                        self.skipTest("Skipping test because '%s' service is"
                                      " not implemented" % (service,))
            func(self, *args, **kwargs)
        return wrapper
    return wrap


class ProviderTestBase(object):

    """
    A dummy base class for Test Cases. Does not inherit from unittest.TestCase
    to avoid confusing test discovery by unittest and nose2. unittest.TestCase
    is injected as a base class by the generator, so calling the unittest
    constructor works correctly.
    """

    def __init__(self, methodName, provider):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.provider = provider

    def setUp(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.setUpMock()

    def tearDown(self):
        if isinstance(self.provider, TestMockHelperMixin):
            self.provider.tearDownMock()


class ProviderTestCaseGenerator():

    """
    Generates test cases for all provider - testcase combinations.
    Detailed docs at test/__init__.py
    """

    def __init__(self, test_classes):
        self.all_test_classes = test_classes
        self.provider_name = os.environ.get("CB_TEST_PROVIDER", "azure")
        self.use_mock_providers = os.environ.get("CB_USE_MOCK_PROVIDERS", False)

    def get_provider_wait_interval(self, provider_class):
        if issubclass(provider_class, TestMockHelperMixin):
            return 0
        else:
            return 1

    def create_provider_instance(self, provider_class):
        """
        Instantiate a default provider instance. All required connection
        settings are expected to be set as environment variables.
        """
        config = {'default_wait_interval':
                  self.get_provider_wait_interval(provider_class),
                  'azure_subscription_id': '7904d702-e01c-4826-8519-f5a25c866a96',
                  'azure_client_Id': '69621fe1-f59f-43de-8799-269007c76b95',
                  'azure_secret': 'Orcw9U5Kd4cUDntDABg0dygN32RQ4FGBYyLRaJ/BlrM=',
                  'azure_tenant': '75ec242e-054d-4b22-98a9-a4602ebb6027'
                  }

        return provider_class(config)

    def generate_new_test_class(self, name, testcase_class):
        """
        Generates a new type which inherits from the given testcase_class and
        unittest.TestCase
        """
        class_name = "{0}{1}".format(name, testcase_class.__name__)
        return type(class_name, (testcase_class, unittest.TestCase), {})

    def generate_test_suite_for_provider_testcase(
            self, provider_class, testcase_class):
        """
        Generate and return a suite of tests for a specific provider class and
        testcase combination
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        suite = unittest.TestSuite()
        for name in testnames:
            generated_cls = self.generate_new_test_class(
                provider_class.__name__,
                testcase_class)
            suite.addTest(
                generated_cls(
                    name,
                    self.create_provider_instance(provider_class)))
        return suite

    def generate_test_suite_for_provider(self, provider_class):
        """
        Generate and return a suite of all available tests for a given provider
        class
        """
        suite = unittest.TestSuite()
        suites = [
            self.generate_test_suite_for_provider_testcase(
                provider_class, test_class)
            for test_class in self.all_test_classes.get(self.provider_name)]
        for s in suites:
            suite.addTest(s)
        return suite

    def generate_tests(self):
        """
        Generate and return a suite of tests for all provider and test class
        combinations
        """
        factory = CloudProviderFactory()
        use_mock_drivers = parse_bool(self.use_mock_providers)
        provider_name = self.provider_name
        if provider_name:
            provider_classes = [
                factory.get_provider_class(
                    provider_name,
                    get_mock=use_mock_drivers)]
            if not provider_classes[0]:
                raise ValueError(
                    "Could not find specified test provider %s" %
                    provider_name)
        else:
            provider_classes = factory.get_all_provider_classes(
                get_mock=use_mock_drivers)
        suite = unittest.TestSuite()
        suites = [
            self.generate_test_suite_for_provider(p) for p in provider_classes]
        for s in suites:
            suite.addTest(s)
        return suite
