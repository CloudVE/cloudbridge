import uuid

import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationSecurityServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group(self):
        sg_name = '{0}'.format(uuid.uuid4())
        print("SG guid - " + sg_name)

        listBeforeCreate = self.provider.security.security_groups.list()
        print("Length Before create - " + str(len(listBeforeCreate)))
        # netId = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96
        # /resourceGroups/CloudBridge-Azure'\
        # '/providers/Microsoft.Network/virtualNetworks/SampleNetwork"
        sg = self.provider.security.security_groups.create(
            name=sg_name, description="testCreateSecGroup", network_id='')
        self.assertEqual(sg_name, sg.name)

        print(str(sg))
        listAfterCreate = self.provider.security.security_groups.list()
        print("Length After create - " + str(len(listAfterCreate)))
        self.assertEqual(len(listAfterCreate), len(listBeforeCreate) + 1)

        get = self.provider.security.security_groups.get(
            "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers'\
            '/Microsoft.Network/networkSecurityGroups/" + sg_name)
        print("Get SG - " + str(get))
        print(str(get.rules))
        self.assertEqual(get.name, sg_name)

        get_notfound = self.provider.security.security_groups.get(
            "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96"
            "/resourceGroups/cloudbridge-azure/providers/Microsoft.Network"
            "/networkSecurityGroups/SecgrupDontFindMe")
        self.assertEqual(get_notfound, None)

        find_exists_list = self.provider.security.security_groups.find(sg_name)
        for sg in find_exists_list:
            self.assertTrue(sg_name in sg.name)
        print("Find - " + str(find_exists_list))
        print("Find Total Results- " + str(find_exists_list.total_results))
        self.assertTrue(find_exists_list.total_results > 0)

        find_not_exists_list = self.provider.security.security_groups. \
            find('dontfindme')
        self.assertTrue(find_not_exists_list.total_results == 0)

        lenBeforeCreateRule = len(sg.rules)
        sg.add_rule('tcp', '1111', '2222', '0.0.0.0/0')
        lenAfterCreateRule = len(sg.rules)
        print("Length before create rule - " + str(lenBeforeCreateRule))
        print("Length after create rule - " + str(lenAfterCreateRule))
        self.assertEqual(lenAfterCreateRule, lenBeforeCreateRule + 1)

        print("create second rule ")
        sg.add_rule('tcp', '1111', '2222', '0.0.0.0/0')
        print("Length before second create rule - " + str(lenBeforeCreateRule))
        print("Length after second create rule - " + str(lenAfterCreateRule))

        print(str(sg.rules))
        get_rule = sg.get_rule('tcp', '1111', '2222', '0.0.0.0/0')
        print("Get Rule - " + str(get_rule))
        self.assertIsNotNone(get_rule)

        get_rule_notfound = sg.get_rule('*', '25', '1', '1')
        self.assertEqual(str(get_rule_notfound), 'None')

        rule_json = sg.rules[0].to_json()
        print("Rule json - " + str(rule_json))
        self.assertIsNotNone(rule_json)

        sg_json = sg.to_json()
        print("SG json - " + str(sg_json))
        self.assertIsNotNone(sg_json)

        listBeforeDeleteFound = self.provider.security.security_groups.list()
        sg_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96" \
                "/resourceGroups/cloudbridge-azure/providers" \
                "/Microsoft.Network/networkSecurityGroups/" + sg_name
        self.provider.security.security_groups.delete(sg_id)
        listAfterDeleteFound = self.provider.security.security_groups.list()
        print("Length before delete - " + str(len(listBeforeDeleteFound)))
        print("Length after delete - " + str(len(listAfterDeleteFound)))
        self.assertEqual(
            len(listAfterDeleteFound), len(listBeforeDeleteFound) - 1)
        sg_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96" \
                "/resourceGroups/cloudbridge-azure/providers" \
                "/Microsoft.Network/networkSecurityGroups/sg5"
        self.provider.security.security_groups.delete(sg_id)
        listAfterDeleteNotFound = self.provider.security.security_groups.list()
        self.assertEqual(
            len(listAfterDeleteNotFound), len(listAfterDeleteFound))
