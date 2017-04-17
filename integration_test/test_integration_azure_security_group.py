import json
import unittest
import uuid

from cloudbridge.cloud.interfaces import TestMockHelperMixin

from test.helpers import ProviderTestBase
import test.helpers as helpers

class AzureIntegrationSecurityServiceTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureIntegrationSecurityServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group(self):
        sg = self.provider.security.security_groups.create(name="testCreateSecGroup", description="testCreateSecGroup", network_id="")
        self.assertEqual("testCreateSecGroup", sg.name)

        list = self.provider.security.security_groups.list()
        self.assertEqual( len(list) , 2)

        get = self.provider.security.security_groups.get("/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure/providers/Microsoft.Network/networkSecurityGroups/testCreateSecGroup")
        self.assertEqual( get.name , "testCreateSecGroup")

        get_notfound = self.provider.security.security_groups.get("testCreateSecGroup1")
        self.assertEqual(get_notfound , None)

        cb = list.data[0]
        rules = cb.rules
        cb.add_rule('*', '25', '100', '*')
        self.assertEqual(len(rules), 3)

        get_rule = cb.get_rule('*', '*', '*', '*')
        self.assertEqual(str(get_rule), "<CBSecurityGroupRule: IP: *; from: *; to: *; grp: None>")

        get_rule_notfound = cb.get_rule('*', '25', '1', '1')
        self.assertEqual(str(get_rule_notfound), 'None')

        rule_json = rules[1].to_json()
        self.assertEqual(rule_json[2:9], "cidr_ip")

        sg_json = cb.to_json()
        self.assertEqual(sg_json[2:4], "id")

        with self.assertRaises(Exception):
            rules[1].delete()

        sg_del = self.provider.security.security_groups.delete("/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure/providers/Microsoft.Network/networkSecurityGroups/testCreateSecGroup")
        self.assertEqual(sg_del, True)

        sg_del_notfound = self.provider.security.security_groups.delete("sg5")
        self.assertEqual(sg_del_notfound, False)