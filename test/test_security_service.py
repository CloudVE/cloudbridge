"""Test cloudbridge.security modules."""
from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import VMFirewall


class CloudSecurityServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_crud_key_pair_service(self):

        def create_kp(name):
            return self.provider.security.key_pairs.create(name=name)

        def cleanup_kp(kp):
            self.provider.security.key_pairs.delete(key_pair_id=kp.id)

        def extra_tests(kp):
            # Recreating existing keypair should raise an exception
            with self.assertRaises(Exception):
                self.provider.security.key_pairs.create(name=kp.name)

        sit.check_crud(self, self.provider.security.key_pairs, KeyPair,
                       "cb_crudkp", create_kp, cleanup_kp,
                       extra_test_func=extra_tests)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_key_pair_properties(self):
        name = 'cb_kpprops-{0}'.format(helpers.get_uuid())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(lambda: kp.delete()):
            self.assertIsNotNone(
                kp.material,
                "KeyPair material is empty but it should not be.")
            # get the keypair again - keypair material should now be empty
            kp = self.provider.security.key_pairs.get(kp.id)
            self.assertIsNone(kp.material,
                              "Keypair material should now be empty")

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_crud_vm_firewall(self):
        name = 'cb_crudfw-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None

        def create_fw(name):
            return self.provider.security.vm_firewalls.create(
                name=name, description=name, network_id=net.id)

        def cleanup_fw(fw):
            fw.delete()

        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net)):
            net, _ = helpers.create_test_network(self.provider, name)

            sit.check_crud(self, self.provider.security.vm_firewalls,
                           VMFirewall, "cb_crudfw", create_fw, cleanup_fw)

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_properties(self):
        name = 'cb_propfw-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, vm_firewall=fw)):
            net, _ = helpers.create_test_network(self.provider, name)
            fw = self.provider.security.vm_firewalls.create(
                name=name, description=name, network_id=net.id)

            self.assertEqual(name, fw.description)

            rule = fw.add_rule(ip_protocol='tcp', from_port=1111, to_port=1111,
                               cidr_ip='0.0.0.0/0')
            found_rule = fw.get_rule(ip_protocol='tcp', from_port=1111,
                                     to_port=1111, cidr_ip='0.0.0.0/0')
            self.assertTrue(
                rule == found_rule,
                "Expected rule {0} not found in VM firewall: {0}".format(
                    rule, fw.rules))

            object_keys = (
                fw.rules[0].ip_protocol,
                fw.rules[0].from_port,
                fw.rules[0].to_port)
            self.assertTrue(
                all(str(key) in repr(fw.rules[0]) for key in object_keys),
                "repr(obj) should contain ip_protocol, form_port, and to_port"
                " so that the object can be reconstructed, but does not:"
                " {0}; {1}".format(fw.rules[0], object_keys))
            self.assertTrue(
                fw == fw,
                "The same VM firewalls should be equal?")
            self.assertFalse(
                fw != fw,
                "The same VM firewalls should still be equal?")

        sit.check_delete(self, self.provider.security.vm_firewalls, fw)
        fwl = self.provider.security.vm_firewalls.list()
        found_fw = [f for f in fwl if f.name == name]
        self.assertTrue(
            len(found_fw) == 0,
            "VM firewall {0} should have been deleted but still exists."
            .format(name))

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_rule_add_twice(self):
        name = 'cb_fwruletwice-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, vm_firewall=fw)):

            net, _ = helpers.create_test_network(self.provider, name)
            fw = self.provider.security.vm_firewalls.create(
                name=name, description=name, network_id=net.id)

            rule = fw.add_rule(ip_protocol='tcp', from_port=1111, to_port=1111,
                               cidr_ip='0.0.0.0/0')
            # attempting to add the same rule twice should succeed
            same_rule = fw.add_rule(ip_protocol='tcp', from_port=1111,
                                    to_port=1111, cidr_ip='0.0.0.0/0')
            self.assertTrue(
                rule == same_rule,
                "Expected rule {0} not found in VM firewall: {0}".format(
                    same_rule, fw.rules))

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_group_rule(self):
        name = 'cb_fwrule-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net, vm_firewall=fw)):
            net, _ = helpers.create_test_network(self.provider, name)
            fw = self.provider.security.vm_firewalls.create(
                name=name, description=name, network_id=net.id)
            self.assertTrue(
                len(fw.rules) == 0,
                "Expected no VM firewall group rule. Got {0}."
                .format(fw.rules))
            rule = fw.add_rule(src_firewall=fw, ip_protocol='tcp', from_port=1,
                               to_port=65535)
            self.assertTrue(
                rule.group.name == name,
                "Expected VM firewall rule name {0}. Got {1}."
                .format(name, rule.group.name))
            for r in fw.rules:
                r.delete()
            fw = self.provider.security.vm_firewalls.get(fw.id)  # update
            self.assertTrue(
                len(fw.rules) == 0,
                "Deleting VMFirewallRule should delete it: {0}".format(
                    fw.rules))
        fwl = self.provider.security.vm_firewalls.list()
        found_fw = [f for f in fwl if f.name == name]
        self.assertTrue(
            len(found_fw) == 0,
            "VM firewall {0} should have been deleted but still exists."
            .format(name))
