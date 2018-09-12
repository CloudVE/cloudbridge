from cloudbridge.cloud.interfaces.resources import FloatingIP
from cloudbridge.cloud.interfaces.resources import Network
from cloudbridge.cloud.interfaces.resources import NetworkState
from cloudbridge.cloud.interfaces.resources import RouterState
from cloudbridge.cloud.interfaces.resources import Subnet
from cloudbridge.cloud.interfaces.resources import SubnetState

import test.helpers as helpers
from test.helpers import ProviderTestBase
from test.helpers import get_provider_test_data
from test.helpers import standard_interface_tests as sit


class CloudNetworkServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['networking.networks'])
    def test_crud_network(self):

        def create_net(label):
            return self.provider.networking.networks.create(
                label=label, cidr_block='10.0.0.0/16')

        def cleanup_net(net):
            if net:
                net.delete()
                net.refresh()
                self.assertTrue(
                    net.state == NetworkState.UNKNOWN,
                    "Network.state must be unknown when refreshing after "
                    "a delete but got %s"
                    % net.state)

        sit.check_crud(self, self.provider.networking.networks, Network,
                       "cb-crudnetwork", create_net, cleanup_net)

    @helpers.skipIfNoService(['networking.networks'])
    def test_network_properties(self):
        label = 'cb-propnetwork-{0}'.format(helpers.get_uuid())
        subnet_label = 'cb-propsubnet-{0}'.format(helpers.get_uuid())
        net = self.provider.networking.networks.create(
            label=label, cidr_block='10.0.0.0/16')
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

            cidr = '10.0.20.0/24'
            sn = net.create_subnet(
                label=subnet_label, cidr_block=cidr,
                zone=helpers.get_provider_test_data(self.provider,
                                                    'placement'))
            with helpers.cleanup_action(lambda: sn.delete()):
                self.assertTrue(
                    sn in net.subnets,
                    "Subnet ID %s should be listed in network subnets %s."
                    % (sn.id, net.subnets))

                self.assertTrue(
                    sn in self.provider.networking.subnets.list(network=net),
                    "Subnet ID %s should be included in the subnets list %s."
                    % (sn.id, self.provider.networking.subnets.list(net))
                )

                self.assertListEqual(
                    net.subnets, [sn],
                    "Network should have exactly one subnet: %s." % sn.id)

                self.assertEqual(
                    net.id, sn.network_id,
                    "Network ID %s and subnet's network id %s should be"
                    " equal." % (net.id, sn.network_id))

                self.assertEqual(
                    net, sn.network,
                    "Network obj %s and subnet's parent net obj %s"
                    " should be equal." % (net, sn.network))

                self.assertEqual(
                    cidr, sn.cidr_block,
                    "Subnet's CIDR %s should match the specified one %s." % (
                        sn.cidr_block, cidr))

    def test_crud_subnet(self):
        # Late binding will make sure that create_subnet gets the
        # correct value
        sn = helpers.get_or_create_default_subnet(self.provider)
        net = sn.network

        def create_subnet(label):
            return self.provider.networking.subnets.create(
                label=label, network=net, cidr_block="10.0.10.0/24",
                zone=helpers.get_provider_test_data(
                    self.provider, 'placement'))

        def cleanup_subnet(subnet):
            if subnet:
                subnet.delete()
                subnet.refresh()
                self.assertTrue(
                    subnet.state == SubnetState.UNKNOWN,
                    "Subnet.state must be unknown when refreshing after "
                    "a delete but got %s"
                    % subnet.state)

        sit.check_crud(self, self.provider.networking.subnets, Subnet,
                       "cb-crudsubnet", create_subnet, cleanup_subnet)

    def test_crud_floating_ip(self):
        gw = helpers.get_test_gateway(
            self.provider)

        def create_fip(label):
            fip = gw.floating_ips.create()
            return fip

        def cleanup_fip(fip):
            if fip:
                gw.floating_ips.delete(fip.id)

        with helpers.cleanup_action(
                lambda: helpers.delete_test_gateway(gw)):
            sit.check_crud(self, gw.floating_ips, FloatingIP,
                           "cb-crudfip", create_fip, cleanup_fip,
                           skip_name_check=True)

    def test_floating_ip_properties(self):
        # Check floating IP address
        gw = helpers.get_test_gateway(
            self.provider)
        fip = gw.floating_ips.create()
        with helpers.cleanup_action(
                lambda: helpers.delete_test_gateway(gw)):
            with helpers.cleanup_action(lambda: fip.delete()):
                fipl = list(gw.floating_ips)
                self.assertIn(fip, fipl)
                # 2016-08: address filtering not implemented in moto
                # empty_ipl = self.provider.network.floating_ips('dummy-net')
                # self.assertFalse(
                #     empty_ipl,
                #     "Bogus network should not have any floating IPs: {0}"
                #     .format(empty_ipl))
                self.assertFalse(
                    fip.private_ip,
                    "Floating IP should not have a private IP value ({0})."
                    .format(fip.private_ip))
                self.assertFalse(
                    fip.in_use,
                    "Newly created floating IP address should not be in use.")

    @helpers.skipIfNoService(['networking.routers'])
    def test_crud_router(self):

        def _cleanup(net, subnet, router, gateway):
            with helpers.cleanup_action(lambda: net.delete()):
                with helpers.cleanup_action(lambda: router.delete()):
                    with helpers.cleanup_action(lambda: subnet.delete()):
                        with helpers.cleanup_action(lambda: gateway.delete()):
                            router.detach_subnet(subnet)
                            router.detach_gateway(gateway)

        label = 'cb-crudrouter-{0}'.format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sn = None
        router = None
        gteway = None
        with helpers.cleanup_action(lambda: _cleanup(net, sn, router, gteway)):
            net = self.provider.networking.networks.create(
                label=label, cidr_block='10.0.0.0/16')
            router = self.provider.networking.routers.create(label=label,
                                                             network=net)
            cidr = '10.0.15.0/24'
            sn = net.create_subnet(label=label, cidr_block=cidr,
                                   zone=helpers.get_provider_test_data(
                                       self.provider, 'placement'))

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

            self.assertTrue(
                len(router.subnets) == 0,
                "No subnet should be attached to router {1}".format(sn, router)
            )
            router.attach_subnet(sn)
            self.assertTrue(
                len(router.subnets) == 1,
                "Subnet {0} not attached to router {1}".format(sn, router)
            )
            gteway = net.gateways.get_or_create_inet_gateway()
            router.attach_gateway(gteway)
            # TODO: add a check for routes after that's been implemented

        sit.check_delete(self, self.provider.networking.routers, router)

    @helpers.skipIfNoService(['networking.networks'])
    def test_default_network(self):
        subnet = self.provider.networking.subnets.get_or_create_default(
            zone=get_provider_test_data(self.provider, 'placement'))
        self.assertIsInstance(subnet, Subnet)
