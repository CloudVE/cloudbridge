"""Test cloudbridge.security modules."""
import json
import unittest
import uuid

from test import helpers
from test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces import TestMockHelperMixin


class CloudSecurityServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_crud_key_pair_service(self):
        name = 'cbtestkeypairA-{0}'.format(uuid.uuid4())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(
            lambda:
                self.provider.security.key_pairs.delete(key_pair_id=kp.id)
        ):
            # test list method
            kpl = self.provider.security.key_pairs.list()
            list_kpl = [i for i in kpl if i.name == name]
            self.assertTrue(
                len(list_kpl) == 1,
                "List key pairs does not return the expected key pair %s" %
                name)

            # check iteration
            iter_kpl = [i for i in self.provider.security.key_pairs
                        if i.name == name]
            self.assertTrue(
                len(iter_kpl) == 1,
                "Iter key pairs does not return the expected key pair %s" %
                name)

            # check find
            find_kp = self.provider.security.key_pairs.find(name=name)[0]
            self.assertTrue(
                find_kp == kp,
                "Find key pair did not return the expected key {0}."
                .format(name))

            # check get
            get_kp = self.provider.security.key_pairs.get(name)
            self.assertTrue(
                get_kp == kp,
                "Get key pair did not return the expected key {0}."
                .format(name))

            # Recreating existing keypair should raise an exception
            with self.assertRaises(Exception):
                self.provider.security.key_pairs.create(name=name)
        kpl = self.provider.security.key_pairs.list()
        found_kp = [k for k in kpl if k.name == name]
        self.assertTrue(
            len(found_kp) == 0,
            "Key pair {0} should have been deleted but still exists."
            .format(name))
        no_kp = self.provider.security.key_pairs.find(name='bogus_kp')
        self.assertFalse(
            no_kp,
            "Found a key pair {0} that should not exist?".format(no_kp))

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_key_pair(self):
        name = 'cbtestkeypairB-{0}'.format(uuid.uuid4())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(lambda: kp.delete()):
            kpl = self.provider.security.key_pairs.list()
            found_kp = [k for k in kpl if k.name == name]
            self.assertTrue(
                len(found_kp) == 1,
                "List key pairs did not return the expected key {0}."
                .format(name))
            self.assertTrue(
                kp.id in repr(kp),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")
            self.assertIsNotNone(
                kp.material,
                "KeyPair material is empty but it should not be.")
            self.assertTrue(
                kp == kp,
                "The same key pair should be equal to self.")
            json_repr = json.dumps(
                {"material": kp.material, "id": name, "name": name},
                sort_keys=True)
            self.assertEqual(
                kp.to_json(), json_repr,
                "JSON key pair representation {0} does not match expected {1}"
                .format(kp.to_json(), json_repr))
        kpl = self.provider.security.key_pairs.list()
        found_kp = [k for k in kpl if k.name == name]
        self.assertTrue(
            len(found_kp) == 0,
            "Key pair {0} should have been deleted but still exists."
            .format(name))

    def cleanup_sg(self, sg, net):
        with helpers.cleanup_action(
                lambda: self.provider.network.delete(network_id=net.id)):
            self.provider.security.security_groups.delete(group_id=sg.id)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_crud_security_group_service(self):
        name = 'CBTestSecurityGroupA-{0}'.format(uuid.uuid4())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sg = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, security_group=sg)):
            net, _ = helpers.create_test_network(self.provider, name)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)

            self.assertEqual(name, sg.description)

            # test list method
            sgl = self.provider.security.security_groups.list()
            found_sgl = [i for i in sgl if i.name == name]
            self.assertTrue(
                len(found_sgl) == 1,
                "List security groups does not return the expected group %s" %
                name)

            # check iteration
            found_sgl = [i for i in self.provider.security.security_groups
                         if i.name == name]
            self.assertTrue(
                len(found_sgl) == 1,
                "Iter security groups does not return the expected group %s" %
                name)

            # check find
            find_sg = self.provider.security.security_groups.find(name=sg.name)
            self.assertTrue(
                len(find_sg) == 1,
                "List security groups returned {0} when expected was: {1}."
                .format(find_sg, sg.name))

            # check get
            get_sg = self.provider.security.security_groups.get(sg.id)
            self.assertTrue(
                get_sg == sg,
                "Get SecurityGroup did not return the expected key {0}."
                .format(name))

            self.assertTrue(
                sg.id in repr(sg),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")
        sgl = self.provider.security.security_groups.list()
        found_sg = [g for g in sgl if g.name == name]
        self.assertTrue(
            len(found_sg) == 0,
            "Security group {0} should have been deleted but still exists."
            .format(name))
        no_sg = self.provider.security.security_groups.find(name='bogus_sg')
        self.assertTrue(
            len(no_sg) == 0,
            "Found a bogus security group?!?".format(no_sg))

    @helpers.skipIfNoService(['security.security_groups'])
    def test_security_group(self):
        """Test for proper creation of a security group."""
        name = 'CBTestSecurityGroupB-{0}'.format(uuid.uuid4())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sg = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, security_group=sg)):
            net, _ = helpers.create_test_network(self.provider, name)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)

            rule = sg.add_rule(ip_protocol='tcp', from_port=1111, to_port=1111,
                               cidr_ip='0.0.0.0/0')
            found_rule = sg.get_rule(ip_protocol='tcp', from_port=1111,
                                     to_port=1111, cidr_ip='0.0.0.0/0')
            self.assertTrue(
                rule == found_rule,
                "Expected rule {0} not found in security group: {0}".format(
                    rule, sg.rules))

            object_keys = (
                sg.rules[0].ip_protocol,
                sg.rules[0].from_port,
                sg.rules[0].to_port)
            self.assertTrue(
                all(str(key) in repr(sg.rules[0]) for key in object_keys),
                "repr(obj) should contain ip_protocol, form_port, and to_port"
                " so that the object can be reconstructed, but does not:"
                " {0}; {1}".format(sg.rules[0], object_keys))
            self.assertTrue(
                sg == sg,
                "The same security groups should be equal?")
            self.assertFalse(
                sg != sg,
                "The same security groups should still be equal?")
#             json_repr = json.dumps(
#                 {"description": name, "name": name, "id": sg.id,
#                  "rules":
#                     [{"from_port": 1111, "group": "", "cidr_ip": "0.0.0.0/0",
#                       "parent": sg.id, "to_port": 1111, "ip_protocol": "tcp",
#                       "id": sg.rules[0].id}]},
#                 sort_keys=True)
#             self.assertTrue(
#                 sg.to_json() == json_repr,
#                 "JSON SG representation {0} does not match expected {1}"
#                 .format(sg.to_json(), json_repr))

        sgl = self.provider.security.security_groups.list()
        found_sg = [g for g in sgl if g.name == name]
        self.assertTrue(
            len(found_sg) == 0,
            "Security group {0} should have been deleted but still exists."
            .format(name))

    @helpers.skipIfNoService(['security.security_groups'])
    def test_security_group_rule_add_twice(self):
        """Test whether adding the same rule twice succeeds."""
        if isinstance(self.provider, TestMockHelperMixin):
            raise unittest.SkipTest(
                "Mock provider returns InvalidParameterValue: "
                "Value security_group is invalid for parameter.")

        name = 'CBTestSecurityGroupC-{0}'.format(uuid.uuid4())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sg = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, security_group=sg)):

            net, _ = helpers.create_test_network(self.provider, name)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)

            rule = sg.add_rule(ip_protocol='tcp', from_port=1111, to_port=1111,
                               cidr_ip='0.0.0.0/0')
            # attempting to add the same rule twice should succeed
            same_rule = sg.add_rule(ip_protocol='tcp', from_port=1111,
                                    to_port=1111, cidr_ip='0.0.0.0/0')
            self.assertTrue(
                rule == same_rule,
                "Expected rule {0} not found in security group: {0}".format(
                    same_rule, sg.rules))

    @helpers.skipIfNoService(['security.security_groups'])
    def test_security_group_group_rule(self):
        """Test for proper creation of a security group rule."""
        name = 'CBTestSecurityGroupD-{0}'.format(uuid.uuid4())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sg = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, security_group=sg)):
            net, _ = helpers.create_test_network(self.provider, name)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)
            self.assertTrue(
                len(sg.rules) == 0,
                "Expected no security group group rule. Got {0}."
                .format(sg.rules))
            rule = sg.add_rule(src_group=sg, ip_protocol='tcp', from_port=1,
                               to_port=65535)
            self.assertTrue(
                rule.group.name == name,
                "Expected security group rule name {0}. Got {1}."
                .format(name, rule.group.name))
            for r in sg.rules:
                r.delete()
            sg = self.provider.security.security_groups.get(sg.id)  # update
            self.assertTrue(
                len(sg.rules) == 0,
                "Deleting SecurityGroupRule should delete it: {0}".format(
                    sg.rules))
        sgl = self.provider.security.security_groups.list()
        found_sg = [g for g in sgl if g.name == name]
        self.assertTrue(
            len(found_sg) == 0,
            "Security group {0} should have been deleted but still exists."
            .format(name))
