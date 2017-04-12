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
    def test_azure_security_group_create(self):
        name = "testCreateSecGroup3"
        sg = self.provider.security.security_groups.create(
            name=name, description=name, network_id="")
        print("Create( " + "Name-" + sg.name + "  Id-" + sg.id + " Rules - " + str(sg.rules) + " )")
        self.assertEqual(name, sg.name)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_list(self):
        sgl = self.provider.security.security_groups.list()
        found_sg = [g.name for g in sgl]
        for group in sgl:
            print("List( " + "Name-" + group.name + "  Id-" + group.id + " Rules - " + " )")
        self.assertTrue(
            len(sgl) == 3,
            "Count should be 3")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_get_found(self):
        sgl = self.provider.security.security_groups.get("sg3")
        print("Get ( " + "Name - " + sgl.name + "  Id - " + sgl.id + " )")
        self.assertTrue(
            sgl.name == "sec_group3",
            "SG name should be sec_group2")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_get_not_found(self):
        sgl = self.provider.security.security_groups.get("sg4")
        print(str(sgl))
        self.assertTrue(
            sgl == None,
            "Security group does not exist. Should return None.")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_delete_IdExists(self):
        sg = self.provider.security.security_groups.delete("sg2")
        print("Delete - ")
        self.assertEqual(sg, True)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_delete_IdNotExist(self):
        sg = self.provider.security.security_groups.delete("sg5")
        self.assertEqual(sg, False)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_create(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        for rule in rules:
            print(str(rule))
        print("Before creating Rule -  " + str(rules[0]) + " length - " + str(len(rules)))
        cb.add_rule('*', '25', '100', '*')
        rules = cb.rules
        print("After creating Rule -  " + str(rules[0]) + " length - " + str(len(rules)))
        self.assertEqual(len(rules), 3)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_delete(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        print("Before deleting Rule -  " + str(rules[0]) + " length - " + str(len(rules)))
        rules[1].delete()
        rules = cb.rules
        print("After deleting Rule -  " + str(rules[0]) + " length - " + str(len(rules)))
        self.assertEqual(len(rules), 2)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_get(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rule = cb.get_rule('*', '25', '1', '100')
        print("Get Rule -  " + str(rule))
        self.assertEqual(str(rule), "<CBSecurityGroupRule: IP: *; from: 25; to: 1; grp: None>")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_to_json(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rule = cb.to_json()
        print("Get Rule -  " + str(rule))
        self.assertEqual(rule[2:4], "id")

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_security_group_rule_to_json(self):
        list = self.provider.security.security_groups.list()
        cb = list.data[0]
        rules = cb.rules
        rule = rules[0]
        json = rule.to_json()
        print("Get Rule -  " + str(json))
        self.assertEqual(json[2:9], "cidr_ip")
