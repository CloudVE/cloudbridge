import unittest

from cloudbridge import factory, interfaces
from cloudbridge.factory import CloudProviderFactory
from cloudbridge.interfaces import TestMockHelperMixin
from cloudbridge.interfaces.provider import CloudProvider
from cloudbridge.providers.aws import AWSCloudProvider


class CloudFactoryTestCase(unittest.TestCase):

    _multiprocess_can_split_ = True

    def test_create_provider_valid(self):
        # Creating a provider with a known name should return
        # a valid implementation
        self.assertIsInstance(CloudProviderFactory().create_provider(
            factory.ProviderList.AWS, {}),
            interfaces.CloudProvider,
            "create_provider did not return a valid VM type")

    def test_create_provider_invalid(self):
        # Creating a provider with an invalid name should raise a
        # NotImplementedError
        with self.assertRaises(NotImplementedError):
            CloudProviderFactory().create_provider("ec23", {})

    def test_get_provider_class_valid(self):
        # Searching for a provider class with a known name should return a
        # valid class
        self.assertEqual(CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS), AWSCloudProvider)

    def test_get_provider_class_invalid(self):
        # Searching for a provider class with an invalid name should
        # return None
        self.assertIsNone(CloudProviderFactory().get_provider_class("aws1"))

    def test_find_provider_include_mocks(self):
        providers = CloudProviderFactory().get_all_provider_classes()
        self.assertTrue(
            any(cls for cls
                in providers
                if issubclass(cls, TestMockHelperMixin)),
            "expected to find at least one mock provider")

    def test_find_provider_exclude_mocks(self):
        for cls in CloudProviderFactory().get_all_provider_classes(
                ignore_mocks=True):
            self.assertTrue(
                not issubclass(cls, TestMockHelperMixin),
                "Did not expect mock but %s implements mock provider" % cls)

    def test_register_provider_class_invalid(self):
        # Attempting to register an invalid test class should be ignored
        class DummyClass(object):
            PROVIDER_ID = 'aws'

        factory = CloudProviderFactory()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass not in
                        factory.get_all_provider_classes())

    def test_register_provider_class_double(self):
        # Attempting to register the same class twice should register second
        # instance
        class DummyClass(CloudProvider):
            PROVIDER_ID = 'aws'

        factory = CloudProviderFactory()
        factory.list_providers()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass in
                        factory.get_all_provider_classes())
        self.assertTrue(AWSCloudProvider not in
                        factory.get_all_provider_classes())

    def test_register_provider_class_without_id(self):
        # Attempting to register a class without a PROVIDER_ID attribute
        # should be ignored.
        class DummyClass(CloudProvider):
            pass

        factory = CloudProviderFactory()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass not in
                        factory.get_all_provider_classes())
