import unittest

from cloudbridge.cloud import factory
from cloudbridge.cloud import interfaces
from cloudbridge.cloud.base.helpers import TestMockHelperMixin
from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces.provider import CloudProvider
from cloudbridge.cloud.providers.aws import AWSCloudProvider
import test.helpers as helpers


class CloudFactoryTestCase(unittest.TestCase):

    def test_create_provider_valid(self):
        """
        Creating a provider with a known name should return
        a valid implementation
        """
        self.assertIsInstance(CloudProviderFactory().create_provider(
            factory.ProviderList.AWS, {}),
            interfaces.CloudProvider,
            "create_provider did not return a valid instance type")

    def test_create_provider_invalid(self):
        """
        Creating a provider with an invalid name should raise a
        NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            CloudProviderFactory().create_provider("ec23", {})

    def test_find_provider_mock_valid(self):
        """
        Searching for a provider with a known mock driver should return
        an implementation implementing helpers.TestMockHelperMixin
        """
        mock = CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS, get_mock=True)
        self.assertTrue(
            issubclass(
                mock,
                helpers.TestMockHelperMixin),
            "Expected mock for AWS but class does not implement mock provider")
        for cls in CloudProviderFactory().get_all_provider_classes(
                get_mock=False):
            self.assertTrue(
                not issubclass(
                    cls,
                    TestMockHelperMixin),
                "Did not expect mock but %s implements mock provider" %
                cls)

    def test_get_provider_class_valid(self):
        """
        Searching for a provider class with a known name should return a valid
        class
        """
        self.assertEqual(CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS), AWSCloudProvider)

    def test_get_provider_class_invalid(self):
        """
        Searching for a provider class with an invalid name should
        return None
        """
        self.assertIsNone(CloudProviderFactory().get_provider_class("aws1"))

    def test_register_test_class_invalid(self):
        """
        Attempting to register an invalid test class should be ignored
        """
        class DummyClass(object):
            SHORT_NAME = 'aws'

        factory = CloudProviderFactory()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass not in
                        factory.get_all_provider_classes(get_mock=False))

    def test_register_test_class_double(self):
        """
        Attempting to register the same class twice should register second
        instance
        """
        class DummyClass(CloudProvider):
            SHORT_NAME = 'aws'

        factory = CloudProviderFactory()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass in
                        factory.get_all_provider_classes(get_mock=False))
        self.assertTrue(AWSCloudProvider not in
                        factory.get_all_provider_classes(get_mock=False))

    def test_register_test_class_without_shortname(self):
        """
        Attempting to register a class without a SHORT_NAME attribute
        should be ignored.
        """
        class DummyClass(CloudProvider):
            pass

        factory = CloudProviderFactory()
        factory.register_provider_class(DummyClass)
        self.assertTrue(DummyClass not in
                        factory.get_all_provider_classes(get_mock=False))
