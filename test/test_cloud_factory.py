import unittest

from pyeventsystem.middleware import intercept

from cloudbridge.cloud import factory
from cloudbridge.cloud import interfaces
from cloudbridge.cloud.base import helpers as cb_helpers
from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import TestMockHelperMixin
from cloudbridge.cloud.interfaces.provider import CloudProvider
from cloudbridge.cloud.providers.aws import AWSCloudProvider


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
        self.assertTrue(
            any(cls for cls
                in CloudProviderFactory().get_all_provider_classes()
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

    def test_middleware_inherited(self):
        return_str = "hello world"
        class SomeDummyClass(object):

            @intercept(event_pattern="*", priority=2499)
            def return_hello_world(self, event_args, *args, **kwargs):
                return return_str

        factory = CloudProviderFactory()
        some_obj = SomeDummyClass()
        factory.add_middleware(some_obj)
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        prov = factory.create_provider(provider_name, {})
        # Any dispatched event should be intercepted and return the string
        self.assertEqual(prov.storage.volumes.get("anything"), return_str)
