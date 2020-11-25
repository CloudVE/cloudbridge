import unittest

import cloudbridge
from cloudbridge import interfaces
from cloudbridge.factory import CloudProviderFactory
from cloudbridge.interfaces import TestMockHelperMixin
from cloudbridge.interfaces.exceptions import ProviderConnectionException

from tests.helpers import ProviderTestBase


class CloudInterfaceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    def test_name_property(self):
        # Name should always return a value and should not raise an exception
        assert self.provider.name

    def test_has_service_valid_service_type(self):
        # has_service with a valid service type should return
        # a boolean and raise no exceptions
        for key, value in interfaces.CloudServiceType.__dict__.items():
            if not key.startswith("__"):
                self.provider.has_service(value)

    def test_has_service_invalid_service_type(self):
        # has_service with an invalid service type should return False
        self.assertFalse(
            self.provider.has_service("NON_EXISTENT_SERVICE"),
            "has_service should not return True for a non-existent service")

    def test_library_version(self):
        # Check that the library version can be retrieved.
        self.assertIsNotNone(cloudbridge.get_version(),
                             "Did not get library version.")

    def test_authenticate_success(self):
        self.assertTrue(self.provider.authenticate())

    def test_authenticate_failure(self):
        if isinstance(self.provider, TestMockHelperMixin):
            raise unittest.SkipTest(
                "Mock providers are not expected to"
                " authenticate correctly")

        # Mock up test by clearing credentials on a per provider basis
        cloned_config = self.provider.config.copy()
        if self.provider.PROVIDER_ID == 'aws':
            cloned_config['aws_access_key'] = "dummy_a_key"
            cloned_config['aws_secret_key'] = "dummy_s_key"
        elif self.provider.PROVIDER_ID == 'openstack':
            cloned_config['os_username'] = "cb_dummy"
            cloned_config['os_password'] = "cb_dummy"
        elif self.provider.PROVIDER_ID == 'azure':
            cloned_config['azure_subscription_id'] = "cb_dummy"
        elif self.provider.PROVIDER_ID == 'gcp':
            cloned_config['gcp_service_creds_dict'] = {'dummy': 'dict'}

        with self.assertRaises(ProviderConnectionException):
            cloned_provider = CloudProviderFactory().create_provider(
                self.provider.PROVIDER_ID, cloned_config)
            cloned_provider.authenticate()

    def test_provider_zone_in_region(self):
        cloned_config = self.provider.config.copy()
        # Just a simpler way set zone to null for any provider
        # instead of doing it individually for each provider
        cloned_config['aws_zone_name'] = None
        cloned_config['azure_zone_name'] = None
        cloned_config['gcp_zone_name'] = None
        cloned_config['os_zone_name'] = None
        cloned_provider = CloudProviderFactory().create_provider(
                self.provider.PROVIDER_ID, cloned_config)
        region = cloned_provider.compute.regions.get(
            cloned_provider.region_name)
        matches = [zone.name for zone in region.zones
                   if zone.name == cloned_provider.zone_name]
        # FIXME: GCP always requires a zone, so skip for now
        if self.provider.PROVIDER_ID != 'gcp':
            self.assertListEqual([cloned_provider.zone_name], matches)

    def test_provider_always_has_zone(self):
        cloned_config = self.provider.config.copy()
        # Just a simpler way set zone to null for any provider
        # instead of doing it individually for each provider
        cloned_config['aws_zone_name'] = None
        cloned_config['azure_zone_name'] = None
        cloned_config['gcp_zone_name'] = None
        cloned_config['os_zone_name'] = None
        cloned_provider = CloudProviderFactory().create_provider(
                self.provider.PROVIDER_ID, cloned_config)
        # FIXME: GCP always requires a zone, so skip for now
        if self.provider.PROVIDER_ID != 'gcp':
            self.assertIsNotNone(cloned_provider.zone_name)
