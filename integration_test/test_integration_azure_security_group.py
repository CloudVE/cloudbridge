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
        sg_name = '{0}'.format(uuid.uuid4())
        print("SG guid - " + sg_name)

        listBeforeCreate = self.provider.security.security_groups.list()
        print("Length Before create - " + str(len(listBeforeCreate)))
        netId = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure'\
        '/providers/Microsoft.Network/virtualNetworks/SampleNetwork"
        sg = self.provider.security.security_groups.create(name=sg_name, description="testCreateSecGroup",
                                                           network_id=netId)
        self.assertEqual(sg_name, sg.name)

        listAfterCreate = self.provider.security.security_groups.list()
        print("Length After create - " + str(len(listAfterCreate)))
        self.assertEqual(len(listAfterCreate), len(listBeforeCreate) + 1)

        get = self.provider.security.security_groups.get(
            "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers'\
            '/Microsoft.Network/networkSecurityGroups/sampleSG")
        print("Get SG - " + str(get))
        print(str(get.rules))
        self.assertEqual(get.name, "sampleSG")

        get_notfound = self.provider.security.security_groups.get(
            "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure'\
            '/providers/Microsoft.Network/networkSecurityGroups/SecgrupDontFindMe")
        self.assertEqual(get_notfound, None)

        find_exists_list = self.provider.security.security_groups.find(sg_name)
        for sg in find_exists_list:
            self.assertTrue(sg_name in sg.name)
        print("Find - " + str(find_exists_list))
        print("Find Total Results- " + str(find_exists_list.total_results))
        self.assertTrue(find_exists_list.total_results > 0)

        find_not_exists_list = self.provider.security.security_groups.find('dontfindme')
        self.assertTrue(find_not_exists_list.total_results == 0)

        cb = listAfterCreate.data[0]
        lenBeforeCreateRule = len(cb.rules)
        cb.add_rule('tcp', '1111', '2222', '0.0.0.0/0')
        lenAfterCreateRule = len(cb.rules)
        self.assertEqual(lenAfterCreateRule, lenBeforeCreateRule+1)

        print(str(cb.rules))
        get_rule = cb.get_rule('tcp', '1111', '2222', '0.0.0.0/0')
        print("Get Rule - " + str(get_rule))
        self.assertEqual(str(get_rule), "<CBSecurityGroupRule: IP: tcp; from: 1111; to: 2222; grp: None>")

        get_rule_notfound = cb.get_rule('*', '25', '1', '1')
        self.assertEqual(str(get_rule_notfound), 'None')

        rule_json = cb.rules[1].to_json()
        print("Rule json - " + str(rule_json))
        self.assertEqual(rule_json[2:9], "cidr_ip")

        sg_json = cb.to_json()
        print("SG json - " + str(sg_json))
        self.assertEqual(sg_json[2:4], "id")

        with self.assertRaises(Exception):
            cb.rules[1].delete()

        listBeforeDeleteFound = self.provider.security.security_groups.list()
        sg_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure/providers'\
        '/Microsoft.Network/networkSecurityGroups/" + sg_name
        sg_del = self.provider.security.security_groups.delete(sg_id)
        listAfterDeleteFound = self.provider.security.security_groups.list()
        print("Length before delete - " + str(len(listBeforeDeleteFound)))
        print("Length after delete - " + str(len(listAfterDeleteFound)))
        self.assertEqual(len(listAfterDeleteFound), len(listBeforeDeleteFound)-1)
        sg_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/cloudbridge-azure/providers'\
        '/Microsoft.Network/networkSecurityGroups/sg5"
        sg_del_notfound = self.provider.security.security_groups.delete(sg_id)
        listAfterDeleteNotFound = self.provider.security.security_groups.list()
        self.assertEqual(len(listAfterDeleteNotFound), len(listAfterDeleteFound))
