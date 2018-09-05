"""Test cloudbridge.security modules."""
import cloudbridge.cloud.base.helpers as cb_helpers
from cloudbridge.cloud.interfaces.exceptions import DuplicateResourceException
from cloudbridge.cloud.interfaces.resources import KeyPair
from cloudbridge.cloud.interfaces.resources import TrafficDirection
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.interfaces.resources import VMFirewallRule

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit


class CloudSecurityServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_crud_key_pair_service(self):

        def create_kp(name):
            return self.provider.security.key_pairs.create(name=name)

        def cleanup_kp(kp):
            if kp:
                self.provider.security.key_pairs.delete(key_pair_id=kp.id)

        def extra_tests(kp):
            # Recreating existing keypair should raise an exception
            with self.assertRaises(DuplicateResourceException):
                self.provider.security.key_pairs.create(name=kp.name)

        sit.check_crud(self, self.provider.security.key_pairs, KeyPair,
                       "cb-crudkp", create_kp, cleanup_kp,
                       extra_test_func=extra_tests)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_key_pair_properties(self):
        name = 'cb-kpprops-{0}'.format(helpers.get_uuid())
        kp = self.provider.security.key_pairs.create(name=name)
        with helpers.cleanup_action(lambda: kp.delete()):
            self.assertIsNotNone(
                kp.material,
                "KeyPair material is empty but it should not be.")
            # get the keypair again - keypair material should now be empty
            kp = self.provider.security.key_pairs.get(kp.id)
            self.assertIsNone(kp.material,
                              "Keypair material should now be empty")

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_import_key_pair(self):
        name = 'cb-kpimport-{0}'.format(helpers.get_uuid())

        public_key, _ = cb_helpers.generate_key_pair()
        kp = self.provider.security.key_pairs.create(
            name=name, public_key_material=public_key)
        with helpers.cleanup_action(lambda: kp.delete()):
            self.assertIsNone(kp.material, "Private KeyPair material should"
                              " be None when key is imported.")

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_crud_vm_firewall(self):

        subnet = helpers.get_or_create_default_subnet(self.provider)
        net = subnet.network

        def create_fw(label):
            return self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

        def cleanup_fw(fw):
            if fw:
                fw.delete()

        sit.check_crud(self, self.provider.security.vm_firewalls,
                       VMFirewall, "cb-crudfw", create_fw, cleanup_fw)

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_properties(self):
        label = 'cb-propfw-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                vm_firewall=fw)):
            subnet = helpers.get_or_create_default_subnet(self.provider)
            net = subnet.network
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

            self.assertEqual(label, fw.description)

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_crud_vm_firewall_rules(self):
        label = 'cb-crudfw-rules-{0}'.format(helpers.get_uuid())

        subnet = helpers.get_or_create_default_subnet(self.provider)
        net = subnet.network

        fw = None
        with helpers.cleanup_action(lambda: fw.delete()):
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

            def create_fw_rule(label):
                return fw.rules.create(
                    direction=TrafficDirection.INBOUND, protocol='tcp',
                    from_port=1111, to_port=1111, cidr='0.0.0.0/0')

            def cleanup_fw_rule(rule):
                if rule:
                    rule.delete()

            sit.check_crud(self, fw.rules, VMFirewallRule, "cb-crudfwrule",
                           create_fw_rule, cleanup_fw_rule,
                           skip_name_check=True)

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_rule_properties(self):
        label = 'cb-propfwrule-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                vm_firewall=fw)):
            subnet = helpers.get_or_create_default_subnet(self.provider)
            net = subnet.network
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

            rule = fw.rules.create(
                direction=TrafficDirection.INBOUND, protocol='tcp',
                from_port=1111, to_port=1111, cidr='0.0.0.0/0')
            self.assertEqual(rule.direction, TrafficDirection.INBOUND)
            self.assertEqual(rule.protocol, 'tcp')
            self.assertEqual(rule.from_port, 1111)
            self.assertEqual(rule.to_port, 1111)
            self.assertEqual(rule.cidr, '0.0.0.0/0')

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_rule_add_twice(self):
        label = 'cb-fwruletwice-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                vm_firewall=fw)):

            subnet = helpers.get_or_create_default_subnet(self.provider)
            net = subnet.network
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

            rule = fw.rules.create(
                direction=TrafficDirection.INBOUND, protocol='tcp',
                from_port=1111, to_port=1111, cidr='0.0.0.0/0')
            # attempting to add the same rule twice should succeed
            same_rule = fw.rules.create(
                direction=TrafficDirection.INBOUND, protocol='tcp',
                from_port=1111, to_port=1111, cidr='0.0.0.0/0')
            self.assertEqual(rule, same_rule)

    @helpers.skipIfNoService(['security.vm_firewalls'])
    def test_vm_firewall_group_rule(self):
        label = 'cb-fwrule-{0}'.format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                vm_firewall=fw)):
            subnet = helpers.get_or_create_default_subnet(self.provider)
            net = subnet.network
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)
            rules = list(fw.rules)
            self.assertTrue(
                # TODO: This should be made consistent across all providers.
                # Currently, OpenStack creates two rules, one for IPV6 and
                # another for IPV4
                len(rules) >= 1, "Expected a single VM firewall rule allowing"
                " all outbound traffic. Got {0}.".format(rules))
            self.assertEqual(
                rules[0].direction, TrafficDirection.OUTBOUND,
                "Expected rule to be outbound. Got {0}.".format(rules))
            rule = fw.rules.create(
                direction=TrafficDirection.INBOUND, src_dest_fw=fw,
                protocol='tcp', from_port=1, to_port=65535)
            self.assertTrue(
                rule.src_dest_fw.label == fw.label,
                "Expected VM firewall rule label {0}. Got {1}."
                .format(fw.label, rule.src_dest_fw.label))
            for r in fw.rules:
                r.delete()
            fw = self.provider.security.vm_firewalls.get(fw.id)  # update
            self.assertTrue(
                len(list(fw.rules)) == 0,
                "Deleting VMFirewallRule should delete it: {0}".format(
                    fw.rules))
        fwl = self.provider.security.vm_firewalls.list()
        found_fw = [f for f in fwl if f.label == label]
        self.assertTrue(
            len(found_fw) == 0,
            "VM firewall {0} should have been deleted but still exists."
            .format(label))
