import unittest

from test.helpers import ProviderTestBase

import cloudbridge

from cloudbridge.cloud import interfaces
from cloudbridge.cloud.factory import CloudProviderFactory
from cloudbridge.cloud.interfaces import TestMockHelperMixin
from cloudbridge.cloud.interfaces.exceptions import ProviderConnectionException


class CloudInterfaceTestCase(ProviderTestBase):

    def test_name_property(self):
        """
        Name should always return a value and should not raise an exception
        """
        assert self.provider.name

    def test_has_service_valid_service_type(self):
        """
        has_service with a valid service type should return
        a boolean and raise no exceptions
        """
        for key, value in interfaces.CloudServiceType.__dict__.items():
            if not key.startswith("__"):
                self.provider.has_service(value)

    def test_has_service_invalid_service_type(self):
        """
        has_service with an invalid service type should return False
        """
        self.assertFalse(
            self.provider.has_service("NON_EXISTENT_SERVICE"),
            "has_service should not return True for a non-existent service")

    def test_library_version(self):
        """
        Check that the library version can be retrieved.
        """
        self.assertIsNotNone(cloudbridge.get_version(),
                             "Did not get library version.")

    def test_authenticate_success(self):
        self.assertTrue(self.provider.authenticate())

    def test_authenticate_failure(self):
        if isinstance(self.provider, TestMockHelperMixin):
            raise unittest.SkipTest(
                "Mock providers are not expected to"
                " authenticate correctly")

        cloned_provider = CloudProviderFactory().create_provider(
            self.provider.PROVIDER_ID, self.provider.config)

        with self.assertRaises(ProviderConnectionException):
            # Mock up test by clearing credentials on a per provider basis
            if cloned_provider.PROVIDER_ID == 'aws':
                cloned_provider.a_key = "dummy_a_key"
                cloned_provider.s_key = "dummy_s_key"
            elif cloned_provider.PROVIDER_ID == 'openstack':
                cloned_provider.username = "cb_dummy"
                cloned_provider.password = "cb_dummy"
            cloned_provider.authenticate()
