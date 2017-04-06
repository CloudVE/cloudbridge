import json
import unittest
import uuid

from cloudbridge.cloud.interfaces import TestMockHelperMixin

from test.helpers import ProviderTestBase
import test.helpers as helpers

class AzureSecurityServiceTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureSecurityServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_list(self):
        print(self.provider)
        sgl = self.provider.security.security_groups.list()
        found_sg = [g.name for g in sgl]
        print("List( " + "Name-" + sgl[0].name + "  Id-" + sgl[0].id + " )")
        self.assertTrue(
            len(sgl) == 3,
            "Security group {0} should have been deleted but still exists.")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_get(self):
        sgl = self.provider.security.security_groups.get("sg2")
        print("Get ( " + "Name - " + sgl.name + "  Id - " + sgl.id + " )")
        self.assertTrue(
            sgl.name == "sec_group2",
            "Security group {0} should have been deleted but still exists.")