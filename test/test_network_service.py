import uuid

from test.helpers import ProviderTestBase
import test.helpers as helpers


class CloudNetworkServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudNetworkServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_network_service(self):
        name = 'cbtestnetwork-{0}'.format(uuid.uuid4())
        subnet_name = 'cbtestsubnet-{0}'.format(uuid.uuid4())
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
        self.assertTrue(
            len(found_net) == 0,
            "Network {0} should have been deleted but still exists."
            .format(name))
