import test.helpers as helpers

from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import Subnet


class CloudNetworkServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['networking.networks'])
    def test_crud_network(self):
        def create_net(name):
            return self.provider.networking.networks.create(
                name=name, cidr_block='10.0.0.0/16')

        def cleanup_net(net):
            self.provider.networking.networks.delete(network_id=net.id)

        sit.check_crud(self, self.provider.networking.networks, Network,
                       "cb_crudnetwork", create_net, cleanup_net)

    @helpers.skipIfNoService(['networking.networks'])
    def test_network_properties(self):
        name = 'cb_propnetwork-{0}'.format(helpers.get_uuid())
        subnet_name = 'cb_propsubnet-{0}'.format(helpers.get_uuid())
        net = self.provider.networking.networks.create(
            name=name, cidr_block='10.0.0.0/16')
        with helpers.cleanup_action(
                lambda: net.delete()
        ):
            net.wait_till_ready()
            self.assertEqual(
                net.state, 'available',
                "Network in state '%s', yet should be 'available'" % net.state)

            sit.check_repr(self, net)

            self.assertIn(
                net.cidr_block, ['', '10.0.0.0/16'],
                "Network CIDR %s does not contain the expected value."
                % net.cidr_block)

            cidr = '10.0.1.0/24'
            sn = net.create_subnet(name=subnet_name, cidr_block=cidr,
                                   zone=helpers.get_provider_test_data(
                                       self.provider, 'placement'))
            with helpers.cleanup_action(lambda: sn.delete()):
                self.assertTrue(
                    sn in net.subnets,
                    "Subnet ID %s should be listed in network subnets %s."
                    % (sn.id, net.subnets))

                self.assertListEqual(
                    net.subnets, [sn],
                    "Network should have exactly one subnet: %s." % sn.id)

                self.assertIn(
                    net.id, sn.network_id,
                    "Network ID %s should be specified in the subnet's network"
                    " id %s." % (net.id, sn.network_id))

                self.assertEqual(
                    cidr, sn.cidr_block,
                    "Subnet's CIDR %s should match the specified one %s." % (
                        sn.cidr_block, cidr))

    def test_crud_subnet(self):
        # Late binding will make sure that create_subnet gets the
        # correct value
        net = None

        def create_subnet(name):
            return self.provider.networking.subnets.create(
                network=net, cidr_block="10.0.0.0/24", name=name)

        def cleanup_subnet(subnet):
            self.provider.networking.subnets.delete(subnet=subnet)

        net_name = 'cb_crudsubnet-{0}'.format(helpers.get_uuid())
        net = self.provider.networking.networks.create(
            name=net_name, cidr_block='10.0.0.0/16')
        with helpers.cleanup_action(
                lambda:
                self.provider.networking.networks.delete(network_id=net.id)
        ):
            sit.check_crud(self, self.provider.networking.subnets, Subnet,
                           "cb_crudsubnet", create_subnet, cleanup_subnet)

    def test_floating_ip_properties(self):
        # Check floating IP address
        ip = self.provider.networking.networks.create_floating_ip()
        ip_id = ip.id
        with helpers.cleanup_action(lambda: ip.delete()):
            ipl = self.provider.networking.networks.floating_ips
            self.assertTrue(
                ip in ipl,
                "Floating IP address {0} should exist in the list {1}"
                .format(ip.id, ipl))
            # 2016-08: address filtering not implemented in moto
            # empty_ipl = self.provider.network.floating_ips('dummy-net')
            # self.assertFalse(
            #     empty_ipl,
            #     "Bogus network should not have any floating IPs: {0}"
            #     .format(empty_ipl))
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
        ipl = self.provider.networking.networks.floating_ips
        found_ip = [a for a in ipl if a.id == ip_id]
        self.assertTrue(
            len(found_ip) == 0,
            "Floating IP {0} should have been deleted but still exists."
            .format(ip_id))

    @helpers.skipIfNoService(['networking.routers'])
    def test_crud_router(self):
        def _cleanup(net, subnet, router, gateway):
            with helpers.cleanup_action(lambda: net.delete()):
                with helpers.cleanup_action(lambda: subnet.delete()):
                    with helpers.cleanup_action(lambda: gateway.delete()):
                        with helpers.cleanup_action(lambda: router.delete()):
                            router.detach_subnet(subnet)
                            router.detach_gateway(gateway)

        name = 'cb_crudrouter-{0}'.format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sn = None
        router = None
        gteway = None
        with helpers.cleanup_action(lambda: _cleanup(net, sn, router, gteway)):
            net = self.provider.networking.networks.create(
                name=name, cidr_block='10.0.0.0/16')
            router = self.provider.networking.routers.create(network=net,
                                                             name=name)
            cidr = '10.0.1.0/24'
            sn = net.create_subnet(name=name, cidr_block=cidr,
                                   zone=helpers.get_provider_test_data(
                                       self.provider, 'placement'))

            # Comment out routers assertion because Azure has dummy
            # implementation for routers
            # and not returns the expected router from the routers method
            # Check basic router properties
            sit.check_standard_behaviour(
                self, self.provider.networking.routers, router)
            self.assertEqual(
                router.state, RouterState.DETACHED,
                "Router {0} state {1} should be {2}.".format(
                    router.id, router.state, RouterState.DETACHED))

            #             self.assertFalse(
            #                 router.network_id,
            #                 "Router {0} should not be assoc. with a network {1}".format(
            #                     router.id, router.network_id))

            router.attach_subnet(sn)
            gteway = (self.provider.networking.gateways
                      .get_or_create_inet_gateway(name))
            router.attach_gateway(gteway)
            # TODO: add a check for routes after that's been implemented

        sit.check_delete(self, self.provider.networking.routers, router)

    @helpers.skipIfNoService(['networking.networks'])
    def test_default_network(self):
        subnet = self.provider.networking.subnets.get_or_create_default()
        self.assertIsInstance(subnet, Subnet)
