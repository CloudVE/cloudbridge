"""Test cloudbridge.security modules."""
import unittest

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.interfaces import TestMockHelperMixin


class CloudSecurityServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_crud_key_pair_service(self):
        name = 'cb_crudkp-{0}'.format(helpers.get_uuid())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(
            lambda:
                self.provider.security.key_pairs.delete(key_pair_id=kp.id)
        ):
            sit.check_standard_behaviour(
                self, self.provider.security.key_pairs, kp)

            # Recreating existing keypair should raise an exception
            with self.assertRaises(Exception):
                self.provider.security.key_pairs.create(name=name)

        sit.check_delete(self, self.provider.security.key_pairs, kp)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_key_pair_properties(self):
        name = 'cb_kpprops-{0}'.format(helpers.get_uuid())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(lambda: kp.delete()):
            self.assertIsNotNone(
                kp.material,
                "KeyPair material is empty but it should not be.")

    def cleanup_sg(self, sg, net):
        with helpers.cleanup_action(
                lambda: self.provider.network.delete(network_id=net.id)):
            self.provider.security.security_groups.delete(group_id=sg.id)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_crud_security_group_service(self):
        name = 'cb_crudsg-{0}'.format(helpers.get_uuid())

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

            sit.check_standard_behaviour(
                self, self.provider.security.security_groups, sg)

        sit.check_delete(self, self.provider.security.security_groups, sg)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_security_group(self):
        """Test for proper creation of a security group."""
        name = 'cb_propsg-{0}'.format(helpers.get_uuid())

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

        sit.check_delete(self, self.provider.security.security_groups, sg)
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

        name = 'cb_sgruletwice-{0}'.format(helpers.get_uuid())

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
        name = 'cb_sgrule-{0}'.format(helpers.get_uuid())

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
