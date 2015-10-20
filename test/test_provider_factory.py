import unittest

from cloudbridge.providers import factory
from cloudbridge.providers import interfaces
from cloudbridge.providers.aws import AWSCloudProviderV1
from cloudbridge.providers.factory import CloudProviderFactory
import test.helpers as helpers


class ProviderFactoryTestCase(unittest.TestCase):

    def test_create_provider_valid(self):
        """
        Creating a provider with a known name should return
        a valid implementation
        """
        self.assertIsInstance(CloudProviderFactory().create_provider(
            factory.ProviderList.AWS, {}, version=1),
            interfaces.CloudProvider,
            "create_provider did not return a valid instance type")

    def test_create_provider_invalid(self):
        """
        Creating a provider with an invalid name should raise a
        NotImplementedError
        """
        with self.assertRaises(NotImplementedError):
            CloudProviderFactory().create_provider("ec23", {})
        with self.assertRaises(NotImplementedError):
            CloudProviderFactory().create_provider(
                factory.ProviderList.AWS,
                {},
                version=100)

    def test_find_provider_impl_valid(self):
        """
        Searching for a provider with a known name or version should return a
        valid implementation
        """
        self.assertTrue(
            CloudProviderFactory().find_provider_impl(
                factory.ProviderList.AWS))
        self.assertEqual(CloudProviderFactory().find_provider_impl(
            factory.ProviderList.AWS, version=1),
            "cloudbridge.providers.aws.AWSCloudProviderV1")

    def test_find_provider_impl_invalid(self):
        """
        Searching for a provider with an invalid name or version should return
        None
        """
        self.assertIsNone(
            CloudProviderFactory().find_provider_impl("openstack1"))
        self.assertIsNone(CloudProviderFactory().find_provider_impl(
            factory.ProviderList.AWS, version=100))

    def test_find_provider_mock_valid(self):
        """
        Searching for a provider with a known mock driver should return
        an implementation implementing helpers.TestMockHelperMixin
        """
        mock = CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS, version=1,
            get_mock=True)
        self.assertTrue(
            issubclass(
                mock,
                helpers.TestMockHelperMixin),
            "Expected mock for AWS but class does not implement mock provider")
        mock = CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS, get_mock=True)
        self.assertTrue(
            issubclass(
                mock,
                helpers.TestMockHelperMixin),
            "Expected mock for AWS but class does not implement mock provider")
        mock = CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS, version=1,
            get_mock=False)
        for cls in CloudProviderFactory().get_all_provider_classes(
                get_mock=False):
            self.assertTrue(
                not issubclass(
                    mock,
                    helpers.TestMockHelperMixin),
                "Did not expect mock but class implements mock provider")

    def test_get_provider_class_valid(self):
        """
        Searching for a provider class with a known name should return a valid
        class
        """
        self.assertTrue(
            CloudProviderFactory().get_provider_class(
                factory.ProviderList.AWS))
        self.assertEqual(CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS, version=1),
            AWSCloudProviderV1)

    def test_get_provider_class_invalid(self):
        """
        Searching for a provider class with an invalid name or version should
        return None
        """
        self.assertIsNone(CloudProviderFactory().get_provider_class("aws1"))
        self.assertIsNone(CloudProviderFactory().get_provider_class(
            factory.ProviderList.AWS,
            version=100))
