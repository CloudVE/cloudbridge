import unittest
from cloudbridge.providers.factory import CloudProviderFactory


class ProviderTestBase(object):

    """
    A dummy base class for Test Cases. Does not inherit from unittest.TestCase
    to avoid confusing test discovery by unittest and nose2. unittest.TestCase
    is injected as a base class by the generator, so calling the unittest constructor
    works correctly.
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
        Instantiate a default provider instance. All required connection settings
        are expected to be set as environment variables.
        """
        return provider_class({})

    def generate_new_test_class(self, name, testcase_class):
        """
        Generates a new type which inherits from the given testcase_class and unittest.TestCase
        """
        class_name = "{0}{1}".format(name, testcase_class.__name__)
        return type(class_name, (testcase_class, unittest.TestCase), {})

    def generate_test_suite_for_provider_testcase(self, provider_class, testcase_class):
        """
        Generate and return a suite of tests for a specific provider class and testcase
        combination
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        suite = unittest.TestSuite()
        for name in testnames:
            generated_cls = self.generate_new_test_class(provider_class.__name__, testcase_class)
            suite.addTest(generated_cls(name, self.create_provider_instance(provider_class)))
        return suite

    def generate_test_suite_for_provider(self, provider_class):
        """
        Generate and return a suite of all available tests for a given provider class
        """
        suite = unittest.TestSuite()
        suites = map(lambda test_class: self.generate_test_suite_for_provider_testcase(
            provider_class, test_class), self.all_test_classes)
        map(suite.addTest, suites)
        return suite

    def generate_tests(self):
        """
        Generate and return a suite of tests for all provider and test class combinations
        """
        factory = CloudProviderFactory()
        provider_classes = factory.get_all_provider_classes()
        suite = unittest.TestSuite()
        suites = map(self.generate_test_suite_for_provider, provider_classes)
        map(suite.addTest, suites)
        return suite
