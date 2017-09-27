import ipaddress

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.factory import ProviderList
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import InvalidConfigurationException
from cloudbridge.cloud.interfaces.exceptions import WaitStateException
from cloudbridge.cloud.interfaces.resources import Instance
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import SnapshotState

import six


class CloudComputeServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.instances', 'networking.networks'])
    def test_crud_instance(self):
        name = "cb_instcrud-{0}".format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        subnet = None

        def create_inst(name):
            return helpers.get_test_instance(self.provider, name,
                                             subnet=subnet)

        def cleanup_inst(inst):
            inst.terminate()
            inst.wait_for([InstanceState.TERMINATED, InstanceState.UNKNOWN])

        def check_deleted(inst):
            deleted_inst = self.provider.compute.instances.get(
                inst.id)
            self.assertTrue(
                deleted_inst is None or deleted_inst.state in (
                    InstanceState.TERMINATED,
                    InstanceState.UNKNOWN),
                "Instance %s should have been deleted but still exists." %
                name)

        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                network=net)):
            net, subnet = helpers.create_test_network(self.provider, name)

            sit.check_crud(self, self.provider.compute.instances, Instance,
                           "cb_instcrud", create_inst, cleanup_inst,
                           custom_check_delete=check_deleted)

    def _is_valid_ip(self, address):
        try:
            ipaddress.ip_address(address)
        except ValueError:
            return False
        return True

    @helpers.skipIfNoService(['compute.instances', 'networking.networks',
                              'security.security_groups',
                              'security.key_pairs'])
    def test_instance_properties(self):
        name = "cb_inst_props-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        net = None
        sg = None
        kp = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net, sg, kp)):
            net, subnet = helpers.create_test_network(self.provider, name)
            kp = self.provider.security.key_pairs.create(name=name)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)
            test_instance = helpers.get_test_instance(self.provider,
                                                      name, key_pair=kp,
                                                      security_groups=[sg],
                                                      subnet=subnet)
            self.assertEqual(
                test_instance.name, name,
                "Instance name {0} is not equal to the expected name"
                " {1}".format(test_instance.name, name))
            image_id = helpers.get_provider_test_data(self.provider, "image")
            self.assertEqual(test_instance.image_id, image_id,
                             "Image id {0} is not equal to the expected id"
                             " {1}".format(test_instance.image_id, image_id))
            self.assertIsInstance(test_instance.zone_id,
                                  six.string_types)
            self.assertEqual(
                test_instance.image_id,
                helpers.get_provider_test_data(self.provider, "image"))
            self.assertIsInstance(test_instance.public_ips, list)
            self.assertIsInstance(test_instance.private_ips, list)
            self.assertEqual(
                test_instance.key_pair_name,
                kp.name)
            self.assertIsInstance(test_instance.security_groups, list)
            self.assertEqual(
                test_instance.security_groups[0],
                sg)
            self.assertIsInstance(test_instance.security_group_ids, list)
            self.assertEqual(
                test_instance.security_group_ids[0],
                sg.id)
            # Must have either a public or a private ip
            ip_private = test_instance.private_ips[0] \
                if test_instance.private_ips else None
            ip_address = test_instance.public_ips[0] \
                if test_instance.public_ips and test_instance.public_ips[0] \
                else ip_private
            self.assertIsNotNone(
                ip_address,
                "Instance must have either a public IP or a private IP")
            self.assertTrue(
                self._is_valid_ip(ip_address),
                "Instance must have a valid IP address")
            self.assertIsInstance(test_instance.instance_type_id,
                                  six.string_types)
            itype = self.provider.compute.instance_types.get(
                test_instance.instance_type_id)
            self.assertEqual(
                itype, test_instance.instance_type,
                "Instance type {0} does not match expected type {1}".format(
                    itype.name, test_instance.instance_type))
            self.assertIsInstance(itype, InstanceType)
            expected_type = helpers.get_provider_test_data(self.provider,
                                                           'instance_type')
            self.assertEqual(
                itype.name, expected_type,
                "Instance type {0} does not match expected type {1}".format(
                    itype.name, expected_type))
            find_zone = [zone for zone in
                         self.provider.compute.regions.current.zones
                         if zone.id == test_instance.zone_id]
            self.assertEqual(len(find_zone), 1,
                             "Instance's placement zone could not be "
                             " found in zones list")

    @helpers.skipIfNoService(['compute.instances', 'compute.images',
                              'compute.instance_types'])
    def test_block_device_mapping_launch_config(self):
        lc = self.provider.compute.instances.create_launch_config()

        # specifying an invalid size should raise
        # an exception
        with self.assertRaises(InvalidConfigurationException):
            lc.add_volume_device(size=-1)

        # Attempting to add a blank volume without specifying a size
        # should raise an exception
        with self.assertRaises(InvalidConfigurationException):
            lc.add_volume_device(source=None)

        # block_devices should be empty so far
        self.assertListEqual(
            lc.block_devices, [], "No block devices should have been"
            " added to mappings list since the configuration was"
            " invalid")

        # Add a new volume
        lc.add_volume_device(size=1, delete_on_terminate=True)

        # Override root volume size
        image_id = helpers.get_provider_test_data(self.provider, "image")
        img = self.provider.compute.images.get(image_id)
        # The size should be greater then the ami size
        # and therefore, img.min_disk is used.
        lc.add_volume_device(
            is_root=True,
            source=img,
            size=img.min_disk if img and img.min_disk else 30,
            delete_on_terminate=True)

        # Attempting to add more than one root volume should raise an
        # exception.
        with self.assertRaises(InvalidConfigurationException):
            lc.add_volume_device(size=1, is_root=True)

        # Attempting to add an incorrect source should raise an exception
        with self.assertRaises(InvalidConfigurationException):
            lc.add_volume_device(
                source="invalid_source",
                delete_on_terminate=True)

        # Add all available ephemeral devices
        instance_type_name = helpers.get_provider_test_data(
            self.provider,
            "instance_type")
        inst_type = self.provider.compute.instance_types.find(
            name=instance_type_name)[0]
        for _ in range(inst_type.num_ephemeral_disks):
            lc.add_ephemeral_device()

        # block_devices should be populated
        self.assertTrue(
            len(lc.block_devices) == 2 + inst_type.num_ephemeral_disks,
            "Expected %d total block devices bit found %d" %
            (2 + inst_type.num_ephemeral_disks, len(lc.block_devices)))

    @helpers.skipIfNoService(['compute.instances', 'compute.images',
                              'compute.instance_types', 'block_store.volumes'])
    def test_block_device_mapping_attachments(self):
        name = "cb_blkattch-{0}".format(helpers.get_uuid())

        if self.provider.PROVIDER_ID == ProviderList.OPENSTACK:
            raise self.skipTest("Not running BDM tests because OpenStack is"
                                " not stable enough yet")

        test_vol = self.provider.block_store.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider,
                                           "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            test_snap = test_vol.create_snapshot(name=name,
                                                 description=name)

            def cleanup_snap(snap):
                snap.delete()
                snap.wait_for([SnapshotState.UNKNOWN],
                              terminal_states=[SnapshotState.ERROR])

            with helpers.cleanup_action(lambda:
                                        cleanup_snap(test_snap)):
                test_snap.wait_till_ready()

                lc = self.provider.compute.instances.create_launch_config()

                # Add a new blank volume
                lc.add_volume_device(size=1, delete_on_terminate=True)

                # Attach an existing volume
                lc.add_volume_device(size=1, source=test_vol,
                                     delete_on_terminate=True)

                # Add a new volume based on a snapshot
                lc.add_volume_device(size=1, source=test_snap,
                                     delete_on_terminate=True)

                # Override root volume size
                image_id = helpers.get_provider_test_data(
                    self.provider,
                    "image")
                img = self.provider.compute.images.get(image_id)
                # The size should be greater then the ami size
                # and therefore, img.min_disk is used.
                lc.add_volume_device(
                    is_root=True,
                    source=img,
                    size=img.min_disk if img and img.min_disk else 30,
                    delete_on_terminate=True)

                # Add all available ephemeral devices
                instance_type_name = helpers.get_provider_test_data(
                    self.provider,
                    "instance_type")
                inst_type = self.provider.compute.instance_types.find(
                    name=instance_type_name)[0]
                for _ in range(inst_type.num_ephemeral_disks):
                    lc.add_ephemeral_device()

                net, subnet = helpers.create_test_network(self.provider, name)

                with helpers.cleanup_action(lambda:
                                            helpers.delete_test_network(net)):

                    inst = helpers.create_test_instance(
                        self.provider,
                        name,
                        subnet=subnet,
                        launch_config=lc)

                    with helpers.cleanup_action(lambda:
                                                helpers.delete_test_instance(
                                                    inst)):
                        try:
                            inst.wait_till_ready()
                        except WaitStateException as e:
                            self.fail("The block device mapped launch did not "
                                      " complete successfully: %s" % e)
                            # TODO: Check instance attachments and make sure they
                            # correspond to requested mappings

    @helpers.skipIfNoService(['compute.instances', 'networking.networks',
                              'security.security_groups'])
    def test_instance_methods(self):
        name = "cb_instmethods-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_inst = None
        net = None
        sg = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_inst, net, sg)):
            net, subnet = helpers.create_test_network(self.provider, name)
            test_inst = helpers.get_test_instance(self.provider, name,
                                                  subnet=subnet)
            sg = self.provider.security.security_groups.create(
                name=name, description=name, network_id=net.id)

            # Check adding a security group to a running instance
            test_inst.add_security_group(sg)
            test_inst.refresh()
            self.assertTrue(
                sg in test_inst.security_groups, "Expected security group '%s'"
                                                 " to be among instance security_groups: [%s]" %
                (sg, test_inst.security_groups))

            # Check removing a security group from a running instance
            test_inst.remove_security_group(sg)
            test_inst.refresh()
            self.assertTrue(
                sg not in test_inst.security_groups, "Expected security group"
                                                     " '%s' to be removed from instance security_groups: [%s]" %
                (sg, test_inst.security_groups))

            # check floating ips
            router = self.provider.networking.routers.create(name, net)
            gateway = None

            def cleanup_router(router, gateway):
                with helpers.cleanup_action(lambda: router.delete()):
                    with helpers.cleanup_action(lambda: gateway.delete()):
                        router.detach_subnet(subnet)
                        router.detach_gateway(gateway)

            with helpers.cleanup_action(lambda: cleanup_router(router,
                                                               gateway)):
                router.attach_subnet(subnet)
                gateway = (self.provider.networking.gateways
                           .get_or_create_inet_gateway(name))
                router.attach_gateway(gateway)
                # check whether adding an elastic ip works
                fip = (self.provider.networking.networks
                       .create_floating_ip())
                with helpers.cleanup_action(lambda: fip.delete()):
                    with helpers.cleanup_action(
                            lambda: test_inst.remove_floating_ip(
                                fip.public_ip)):
                        test_inst.add_floating_ip(fip.public_ip)
                        test_inst.refresh()
                        # On Devstack, FloatingIP is listed under private_ips.
                        self.assertIn(fip.public_ip, test_inst.public_ips +
                                      test_inst.private_ips)
                    test_inst.refresh()
                    self.assertNotIn(
                        fip.public_ip,
                        test_inst.public_ips + test_inst.private_ips)
