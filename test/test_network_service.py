import test.helpers as helpers
import uuid
from test.helpers import ProviderTestBase


class CloudNetworkServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudNetworkServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_network_service(self):
        name = 'cbtestnetworkservice-{0}'.format(uuid.uuid4())
        subnet_name = 'cbtestsubnetservice-{0}'.format(uuid.uuid4())
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

            # check subnet
            subnet = self.provider.network.subnets.create(
                network=net, cidr_block="10.0.0.1/24", name=subnet_name)
            with helpers.cleanup_action(
                lambda:
                    self.provider.network.subnets.delete(subnet=subnet)
            ):
                # test list method
                subnetl = self.provider.network.subnets.list(network=net)
                list_subnetl = [n for n in subnetl if n.name == subnet_name]
                self.assertTrue(
                    len(list_subnetl) == 1,
                    "List subnets does not return the expected subnet %s" %
                    subnet_name)

            subnetl = self.provider.network.subnets.list()
            found_subnet = [n for n in subnetl if n.name == subnet_name]
            self.assertTrue(
                len(found_subnet) == 0,
                "Subnet {0} should have been deleted but still exists."
                .format(subnet_name))

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

    def test_crud_network(self):
        name = 'cbtestnetwork-{0}'.format(uuid.uuid4())
        subnet_name = 'cbtestsubnet-{0}'.format(uuid.uuid4())
        net = self.provider.network.create(name=name)
        with helpers.cleanup_action(
            lambda: net.delete()
        ):
            net.wait_till_ready()
            self.assertEqual(
                net.refresh(), 'available',
                "Network in state %s , yet should be 'available'" % net.state)

            self.assertIn(
                net.id, repr(net),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not.")

            self.assertIn(
                net.cidr_block, ['', '10.0.0.0/16'],
                "Network CIDR %s does not contain the expected value."
                % net.cidr_block)

            cidr = '10.0.1.0/24'
            sn = net.create_subnet(cidr_block=cidr, name=subnet_name)
            with helpers.cleanup_action(lambda: sn.delete()):
                self.assertTrue(
                    sn.id in [s.id for s in net.subnets()],
                    "Subnet ID %s should be listed in network subnets %s."
                    % (sn.id, net.subnets()))

                self.assertIn(
                    net.id, sn.network_id,
                    "Network ID %s should be specified in the subnet's network"
                    " id %s." % (net.id, sn.network_id))

                self.assertEqual(
                    cidr, sn.cidr_block,
                    "Subnet's CIDR %s should match the specified one %s." % (
                        sn.cidr_block, cidr))
