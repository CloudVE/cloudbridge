import cloudbridge.cloud.providers.azure.test.helpers as helpers
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureSecurityServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_create(self):
        name = "testCreateSecGroup3"
        sg = self.provider.security.security_groups.create(
            name=name, description=name, network_id="")
        print("Create - " + str(sg))
        self.assertEqual(name, sg.name)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_create_and_delete(self):
        name = "testCreateSecGroup10"
        sg = self.provider.security.security_groups.create(
            name=name, description=name, network_id="")
        print("Create - " + str(sg))
        self.assertEqual(name, sg.name)
        deleted = sg.delete()
        self.assertTrue(deleted)
        deleted = sg.delete()
        self.assertFalse(deleted)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_create_no_description(self):
        name = "testCreateSecGroup13"
        sg = self.provider.security.security_groups.create(
            name=name, description=None, network_id="")
        print("Create - " + str(sg))
        self.assertEqual(name, sg.name)
        sg.description = name
        sg.name = 'NewName'
        self.assertEqual(name, sg.description)
        self.provider.security.security_groups.delete('testCreateSecGroup13')

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_find_exists(self):
        sgl = self.provider.security.security_groups.find("sg3")
        for sg in sgl:
            self.assertTrue("sg" in sg.name)
        self.assertTrue(sgl.total_results > 0)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_find_not_exists(self):
        sgl = self.provider.security.security_groups.find('dontfindme')
        self.assertTrue(sgl.total_results == 0)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_list(self):
        sgl = self.provider.security.security_groups.list()
        for group in sgl:
            print("List - " + str(group))
        self.assertTrue(
            len(sgl) == 3,
            "Count should be 3")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_get_found(self):
        sgl = self.provider.security.security_groups.get('sg3')
        print("Get ( " + "Name - " + sgl.name + "  Id - " + sgl.id + " )")
        self.assertTrue(
            sgl.name == "sg3",
            "SG name should be sg3")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_get_not_found(self):
        sgl = self.provider.security.security_groups.get('sg4')
        print(str(sgl))
        self.assertTrue(
            sgl is None,
            "Security group does not exist. Should return None.")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_delete_IdExists(self):
        deleted = self.provider.security.security_groups.delete('sg2')
        print("Delete - ")
        self.assertEqual(deleted, True)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_delete_IdNotExist(self):
        deleted = self.provider.security.security_groups.delete('sg5')
        self.assertEqual(deleted, False)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_create(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        for rule in rules:
            print(str(rule))
        print("Before creating Rule length - " + str(len(rules)))
        cb.add_rule('*', '25', '100', '*')
        rules = cb.rules
        print("After creating Rule length - " + str(len(rules)))
        self.assertEqual(len(rules), 3)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_create_twice(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        first_rule = cb.add_rule('*', '25', '100')
        second_rule = cb.add_rule('*', '25', '100')
        self.assertEqual(first_rule, second_rule)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_delete(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        print("Before deleting Rule length - " + str(len(rules)))
        rules[1].delete()
        rules = cb.rules
        print("After deleting Rule length - " + str(len(rules)))
        self.assertEqual(len(rules), 4)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_get_exist(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rule = cb.get_rule('*', '25', '1', '100')
        print("Get Rule -  " + str(rule))
        self.assertIsNotNone(rule)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_get_notExist(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rule = cb.get_rule('*', '25', '1', '1')
        print("Get Rule -  " + str(rule))
        self.assertEqual(str(rule), 'None')

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_to_json(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rule = cb.to_json()
        print("Get Rule -  " + str(rule))
        self.assertIsNotNone(rule)
        cb = list.data[1]
        rule = cb.to_json()
        self.assertIsNotNone(rule)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_to_json(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        rule = rules[0]
        json = rule.to_json()
        print("Get Rule -  " + str(json))
        self.assertEqual(json[2:9], "cidr_ip")
