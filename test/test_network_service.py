import uuid

from test.helpers import ProviderTestBase
import test.helpers as helpers


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
            subnet = self.provider.network.create_subnet(
                network=net, cidr_block="10.0.0.1/24", name=subnet_name)
            with helpers.cleanup_action(
                lambda:
                    self.provider.network.delete_subnet(subnet=subnet)
            ):
                # test list method
                subnetl = self.provider.network.list_subnets()
                list_subnetl = [n for n in subnetl if n.name == subnet_name]
                self.assertTrue(
                    len(list_subnetl) == 1,
                    "List subnets does not return the expected subnet %s" %
                    subnet_name)

            subnetl = self.provider.network.list_subnets()
            found_subnet = [n for n in subnetl if n.name == subnet_name]
            self.assertTrue(
                len(found_subnet) == 0,
                "Subnet {0} should have been deleted but still exists."
                .format(subnet_name))

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
                # Does not work with moto until filter 'vpcId' for
                # DescribeSubnets is not implemented.
                # self.assertTrue(
                #     sn.id in [s.id for s in net.subnets()],
                #     "Subnet ID %s should be listed in network subnets %s."
                #     % (sn.id, net.subnets()))

                self.assertIn(
                    net.id, sn.network_id,
                    "Network ID %s should be specified in the subnet's network"
                    " id %s." % (net.id, sn.network_id))

                self.assertEqual(
                    cidr, sn.cidr_block,
                    "Subnet's CIDR %s should match the specified one %s." % (
                        sn.cidr_block, cidr))
