import unittest

from cloudbridge.cloud import factory
from cloudbridge.cloud import interfaces
from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.providers.aws import AWSCloudProvider
import test.helpers as helpers


class ProviderFactoryTestCase(unittest.TestCase):

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

    def test_find_provider_impl_valid(self):
        """
        Searching for a provider with a known name should return a
        valid implementation
        """
        self.assertEqual(CloudProviderFactory().find_provider_impl(
            factory.ProviderList.AWS),
            "cloudbridge.cloud.providers.aws.AWSCloudProvider")

    def test_find_provider_impl_invalid(self):
        """
        Searching for a provider with an invalid name should return
        None
        """
        self.assertIsNone(
            CloudProviderFactory().find_provider_impl("openstack1"))

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
                    helpers.TestMockHelperMixin),
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
