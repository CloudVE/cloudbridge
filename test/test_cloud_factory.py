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
        start_count = 10

        class SomeDummyClass(object):
            count = start_count

            @intercept(event_pattern="*", priority=2499)
            def return_incremented(self, event_args, *args, **kwargs):
                self.count += 1
                return self.count

        factory = CloudProviderFactory()
        some_obj = SomeDummyClass()
        factory.middleware.add(some_obj)
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        first_prov = factory.create_provider(provider_name, {})
        # Any dispatched event should be intercepted and increment the count
        first_prov.storage.volumes.get("anything")
        self.assertEqual(first_prov.networking.networks.get("anything"),
                         start_count + 2)
        second_prov = factory.create_provider(provider_name, {})
        # This count should be independent of the previous one
        self.assertEqual(second_prov.networking.networks.get("anything"),
                         start_count + 3)

    def test_middleware_inherited_constructor(self):
        start_count = 10
        increment = 2

        class SomeDummyClass(object):
            count = start_count

            @intercept(event_pattern="*", priority=2499)
            def return_incremented(self, event_args, *args, **kwargs):
                self.count += 1
                return self.count

        factory = CloudProviderFactory()
        factory.middleware.add_constructor(SomeDummyClass)
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        first_prov = factory.create_provider(provider_name, {})
        # Any dispatched event should be intercepted and increment the count
        first_prov.storage.volumes.get("anything")
        self.assertEqual(first_prov.networking.networks.get("anything"),
                         start_count + 2)
        second_prov = factory.create_provider(provider_name, {})
        # This count should be independent of the previous one
        self.assertEqual(second_prov.networking.networks.get("anything"),
                         start_count + 1)

        class SomeDummyClassWithArgs(object):
            def __init__(self, start, increment):
                self.count = start
                self.increment = increment

            @intercept(event_pattern="*", priority=2499)
            def return_incremented(self, event_args, *args, **kwargs):
                self.count += self.increment
                return self.count

        factory = CloudProviderFactory()
        factory.middleware.add_constructor(SomeDummyClassWithArgs,
                                           start_count, increment)
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        first_prov = factory.create_provider(provider_name, {})
        # Any dispatched event should be intercepted and increment the count
        first_prov.storage.volumes.get("anything")
        self.assertEqual(first_prov.networking.networks.get("anything"),
                         start_count + 2*increment)
        second_prov = factory.create_provider(provider_name, {})
        # This count should be independent of the previous one
        self.assertEqual(second_prov.networking.networks.get("anything"),
                         start_count + increment)

    def test_middleware_inherited_events(self):

        class SomeDummyClass(object):

            @intercept(event_pattern="*", priority=2499)
            def return_goodbye(self, event_args, *args, **kwargs):
                return "goodbye"

        def return_hello(event_args, *args, **kwargs):
            return "hello"

        factory = CloudProviderFactory()
        factory.middleware.add(SomeDummyClass())
        factory.middleware.events.intercept("*", 2490, return_hello)
        provider_name = cb_helpers.get_env("CB_TEST_PROVIDER", "aws")
        prov = factory.create_provider(provider_name, {})
        # Any dispatched event should be intercepted and return "hello" instead
        self.assertEqual(prov.networking.networks.get("anything"),
                         "hello")
