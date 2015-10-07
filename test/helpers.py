from contextlib import contextmanager
import os
import sys
import unittest

from cloudbridge.providers.factory import CloudProviderFactory


@contextmanager
def exception_action(cleanup_func):
    """
    Context manager to carry out a given
    cleanup action when an exception occurs.
    If any errors occur during the cleanup
    action, those are ignored, and the original
    traceback is preserved.

    :params func: This function is called only
        if an exception occurs. Any exceptions raised
        by func are ignored.
    Usage:
        with exception_action(lambda e: print("Oops!")):
            do_something()
    """
    try:
        yield
    except:
        _, ex_val, ex_traceback = sys.exc_info()
        try:
            cleanup_func()
        except:
            pass
        # raise the original exception
        raise ex_val.with_traceback(ex_traceback)


def create_test_instance(provider):
    instance_name = "HelloCloudBridge-{0}".format(provider.name)
    if "AWSCloudProvider" in provider.name:
        ami = os.environ.get('CB_AMI', 'ami-d85e75b0')
        instance_type = os.environ.get('CB_INSTANCE_TYPE', 't1.micro')
        return provider.compute.create_instance(
            instance_name, ami, instance_type)
    elif "OpenStackCloudProvider" in provider.name:
        image_id = os.environ.get(
            'CB_IMAGE',
            "d57696ba-5ed2-43fe-bf78-a587829973a9")
        instance_type = os.environ.get('CB_FLAVOR', "m2.xsmall")
        return provider.compute.create_instance(
            "{0}-{1}".format(instance_name, provider.name),
            image_id,
            instance_type)


def get_test_instance(provider):
    instance = create_test_instance(provider)
    instance.wait_till_ready()
    return instance


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


class ProviderTestCaseGenerator():

    """
    Generates test cases for all provider - testcase combinations.
    Detailed docs at test/__init__.py
    """

    def __init__(self, test_classes):
        self.all_test_classes = test_classes

    def create_provider_instance(self, provider_class):
        """
        Instantiate a default provider instance. All required connection
        settings are expected to be set as environment variables.
        """
        return provider_class({})

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
        suites = map(
            lambda test_class: self.generate_test_suite_for_provider_testcase(
                provider_class, test_class), self.all_test_classes)
        map(suite.addTest, suites)
        return suite

    def generate_tests(self):
        """
        Generate and return a suite of tests for all provider and test class
        combinations
        """
        factory = CloudProviderFactory()
        provider_name = os.environ.get("CB_TEST_PROVIDER", None)
        if provider_name:
            provider_classes = [factory.get_provider_class(provider_name)]
            if not provider_classes[0]:
                raise ValueError(
                    "Could not find specified test provider %s" %
                    provider_name)
        else:
            provider_classes = factory.get_all_provider_classes()
        suite = unittest.TestSuite()
        suites = map(self.generate_test_suite_for_provider, provider_classes)
        map(suite.addTest, suites)
        return suite
