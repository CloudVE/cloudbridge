import uuid

from cloudbridge.cloud.providers.azure.integration_test import helpers
from cloudbridge.cloud.providers.azure. \
    integration_test.helpers import ProviderTestBase


class AzureIntegrationNetworkServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['network'])
    def test_crud_network_service(self):
        name = 'intgtestnetworkservice-{0}'.format(uuid.uuid4().hex[:6])
        net = self.provider.network.create(name=name)
        with helpers.cleanup_action(
                lambda:
                self.provider.network.delete(network_id=net.id)
        ):
            # test list method
            netl = self.provider.network.list()
            list_netl = [n for n in netl if n.name == name]
            self.assertTrue(
                len(list_netl) == 1,
                "List networks does not return the expected network %s" %
                name)

            # check get
            get_net = self.provider.network.get(network_id=net.id)
            self.assertTrue(
                get_net == net,
                "Get network did not return the expected network {0}."
                .format(name))

            # Check floating IP address
            ip = self.provider.network.create_floating_ip()
            ip_id = ip.id
            with helpers.cleanup_action(lambda: ip.delete()):
                ipl = self.provider.network.floating_ips()
                self.assertTrue(
                    ip in ipl,
                    "Floating IP address {0} should exist in the list {1}"
                    .format(ip.id, ipl))
                self.assertIn(
                    ip.public_ip, repr(ip),
                    "repr(obj) should contain the address public IP value.")
                self.assertFalse(
                    ip.private_ip,
                    "Floating IP should not have a private IP value ({0})."
                        .format(ip.private_ip))
                self.assertFalse(
                    ip.in_use(),
                    "Newly created floating IP address should not be in use.")
            ipl = self.provider.network.floating_ips()
            found_ip = [a for a in ipl if a.id == ip_id]
            self.assertTrue(
                len(found_ip) == 0,
                "Floating IP {0} should have been deleted but still exists."
                .format(ip_id))

        netl = self.provider.network.list()
        found_net = [n for n in netl if n.name == name]
        self.assertEqual(
            len(found_net), 0,
            "Network {0} should have been deleted but still exists."
                .format(name))
