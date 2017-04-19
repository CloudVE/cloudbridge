import json
import unittest
import uuid

from cloudbridge.cloud.interfaces import TestMockHelperMixin

from test.helpers import ProviderTestBase
import test.helpers as helpers


class AzureResourceGroupTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureResourceGroupTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_resource_group_create(self):
        resource_group_params = {'location': self.provider.region_name}
        rg = self.provider._azure_client.create_resource_group(self.provider.resource_group, resource_group_params)
        print("Create Resource - " + str(rg))
        self.assertTrue(
            rg.name == "cloudbridge-azure",
            "Resource Group should be Cloudbridge")

    def test_resource_group_get(self):
        rg = self.provider._azure_client.get_resource_group('MyGroup')
        print("Get Resource - " + str(rg))
        self.assertTrue(
            rg.name == "testResourceGroup",
            "Resource Group should be Cloudbridge")
