import test.helpers as helpers
import uuid
from test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces.resources import RouterState


class CloudNetworkServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['network'])
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
                # test get method
                sn = self.provider.network.subnets.get(subnet.id)
                self.assertTrue(
                    subnet.id == sn.id,
                    "GETting subnet should return the same subnet")

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

    @helpers.skipIfNoService(['network'])
    def test_crud_network(self):
        name = 'cbtestnetwork-{0}'.format(uuid.uuid4())
        subnet_name = 'cbtestsubnet-{0}'.format(uuid.uuid4())
        net = self.provider.network.create(name=name)
        with helpers.cleanup_action(
            lambda: net.delete()
        ):
            net.wait_till_ready()
            self.assertEqual(
                net.state, 'available',
                "Network in state '%s', yet should be 'available'" % net.state)

            self.assertIn(
                net.id, repr(net),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not.")

            self.assertIn(
                net.cidr_block, ['', '10.0.0.0/16'],
                "Network CIDR %s does not contain the expected value."
                % net.cidr_block)

            cidr = '10.0.1.0/24'
            sn = net.create_subnet(
                cidr_block=cidr, name=subnet_name,
                zone=helpers.get_provider_test_data(self.provider,
                                                    'placement'))
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

    @helpers.skipIfNoService(['network.routers'])
    def test_crud_router(self):

        def _cleanup(net, subnet, router):
            with helpers.cleanup_action(lambda: net.delete()):
                with helpers.cleanup_action(lambda: subnet.delete()):
                    with helpers.cleanup_action(lambda: router.delete()):
                        router.remove_route(subnet.id)
                        router.detach_network()

        name = 'cbtestrouter-{0}'.format(uuid.uuid4())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        sn = None
        router = None
        with helpers.cleanup_action(lambda: _cleanup(net, sn, router)):
            router = self.provider.network.create_router(name=name)
            net = self.provider.network.create(name=name)
            cidr = '10.0.1.0/24'
            sn = net.create_subnet(cidr_block=cidr, name=name,
                                   zone=helpers.get_provider_test_data(
                                       self.provider, 'placement'))

            # Check basic router properties
            self.assertIn(
                router, self.provider.network.routers(),
                "Router {0} should exist in the router list {1}.".format(
                    router.id, self.provider.network.routers()))
            self.assertIn(
                router.id, repr(router),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not.")
            self.assertEqual(
                router.name, name,
                "Router {0} name should be {1}.".format(router.name, name))
            self.assertEqual(
                router.state, RouterState.DETACHED,
                "Router {0} state {1} should be {2}.".format(
                    router.id, router.state, RouterState.DETACHED))
            self.assertFalse(
                router.network_id,
                "Router {0} should not be assoc. with a network {1}".format(
                    router.id, router.network_id))

            # TODO: Cloud specific code, needs fixing
            # Check router connectivity
            # On OpenStack only one network is external and on AWS every
            # network is external, yet we need to use the one we've created?!
            if self.provider.PROVIDER_ID == 'openstack':
                for n in self.provider.network.list():
                    if n.external:
                        external_net = n
                        break
            else:
                external_net = net
            router.attach_network(external_net.id)
            router.refresh()
            self.assertEqual(
                router.network_id, external_net.id,
                "Router should be attached to network {0}, not {1}".format(
                    external_net.id, router.network_id))
            router.add_route(sn.id)
            # TODO: add a check for routes after that's been implemented

        routerl = self.provider.network.routers()
        found_router = [r for r in routerl if r.name == name]
        self.assertEqual(
            len(found_router), 0,
            "Router {0} should have been deleted but still exists."
            .format(name))
