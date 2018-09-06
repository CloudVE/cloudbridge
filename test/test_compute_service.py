import ipaddress

import six

from cloudbridge.cloud.factory import ProviderList
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import InvalidConfigurationException
from cloudbridge.cloud.interfaces.exceptions import WaitStateException
from cloudbridge.cloud.interfaces.resources import Instance
from cloudbridge.cloud.interfaces.resources import SnapshotState
from cloudbridge.cloud.interfaces.resources import VMType

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit


class CloudComputeServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['compute.instances', 'networking.networks'])
    def test_crud_instance(self):
        label = "cb-instcrud-{0}".format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        subnet = None

        def create_inst(label):
            # Also test whether sending in an empty_dict for user_data
            # results in an automatic conversion to string.
            return helpers.get_test_instance(self.provider, label,
                                             subnet=subnet, user_data={})

        def cleanup_inst(inst):
            if inst:
                inst.delete()
                inst.wait_for([InstanceState.DELETED, InstanceState.UNKNOWN])
                inst.refresh()
                self.assertTrue(
                    inst.state == InstanceState.UNKNOWN,
                    "Instance.state must be unknown when refreshing after a "
                    "delete but got %s"
                    % inst.state)

        def check_deleted(inst):
            deleted_inst = self.provider.compute.instances.get(
                inst.id)
            self.assertTrue(
                deleted_inst is None or deleted_inst.state in (
                    InstanceState.DELETED,
                    InstanceState.UNKNOWN),
                "Instance %s should have been deleted but still exists." %
                label)

        subnet = helpers.get_or_create_default_subnet(self.provider)

        sit.check_crud(self, self.provider.compute.instances, Instance,
                       "cb-instcrud", create_inst, cleanup_inst,
                       custom_check_delete=check_deleted)

    def _is_valid_ip(self, address):
        try:
            ipaddress.ip_address(address)
        except ValueError:
            return False
        return True

    @helpers.skipIfNoService(['compute.instances', 'networking.networks',
                              'security.vm_firewalls',
                              'security.key_pairs'])
    def test_instance_properties(self):
        label = "cb-inst-props-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        fw = None
        kp = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, fw, kp)):
            subnet = helpers.get_or_create_default_subnet(self.provider)
            net = subnet.network
            kp = self.provider.security.key_pairs.create(name=label)
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)
            test_instance = helpers.get_test_instance(self.provider,
                                                      label, key_pair=kp,
                                                      vm_firewalls=[fw],
                                                      subnet=subnet)
            self.assertEqual(
                test_instance.label, label,
                "Instance label {0} is not equal to the expected label"
                " {1}".format(test_instance.label, label))
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
            if test_instance.public_ips:
                self.assertTrue(
                    test_instance.public_ips[0], "public ip should contain a"
                    " valid value if a list of public_ips exist")
            self.assertIsInstance(test_instance.private_ips, list)
            self.assertTrue(test_instance.private_ips[0], "private ip should"
                            " contain a valid value")
            self.assertEqual(
                test_instance.key_pair_id,
                kp.id)
            self.assertIsInstance(test_instance.vm_firewalls, list)
            self.assertEqual(
                test_instance.vm_firewalls[0],
                fw)
            self.assertIsInstance(test_instance.vm_firewall_ids, list)
            self.assertEqual(
                test_instance.vm_firewall_ids[0],
                fw.id)
            # Must have either a public or a private ip
            ip_private = test_instance.private_ips[0] \
                if test_instance.private_ips else None
            ip_address = test_instance.public_ips[0] \
                if test_instance.public_ips and test_instance.public_ips[0] \
                else ip_private
            # Convert to unicode for py27 compatibility with ipaddress()
            ip_address = u"{}".format(ip_address)
            self.assertIsNotNone(
                ip_address,
                "Instance must have either a public IP or a private IP")
            self.assertTrue(
                self._is_valid_ip(ip_address),
                "Instance must have a valid IP address. Got: %s" % ip_address)
            self.assertIsInstance(test_instance.vm_type_id,
                                  six.string_types)
            vm_type = self.provider.compute.vm_types.get(
                test_instance.vm_type_id)
            self.assertEqual(
                vm_type, test_instance.vm_type,
                "VM type {0} does not match expected type {1}".format(
                    vm_type.name, test_instance.vm_type))
            self.assertIsInstance(vm_type, VMType)
            expected_type = helpers.get_provider_test_data(self.provider,
                                                           'vm_type')
            self.assertEqual(
                vm_type.name, expected_type,
                "VM type {0} does not match expected type {1}".format(
                    vm_type.name, expected_type))
            find_zone = [zone for zone in
                         self.provider.compute.regions.current.zones
                         if zone.id == test_instance.zone_id]
            self.assertEqual(len(find_zone), 1,
                             "Instance's placement zone could not be "
                             " found in zones list")

    @helpers.skipIfNoService(['compute.instances', 'compute.images',
                              'compute.vm_types'])
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
        vm_type_name = helpers.get_provider_test_data(
            self.provider,
            "vm_type")
        vm_type = self.provider.compute.vm_types.find(
            name=vm_type_name)[0]
        for _ in range(vm_type.num_ephemeral_disks):
            lc.add_ephemeral_device()

        # block_devices should be populated
        self.assertTrue(
            len(lc.block_devices) == 2 + vm_type.num_ephemeral_disks,
            "Expected %d total block devices bit found %d" %
            (2 + vm_type.num_ephemeral_disks, len(lc.block_devices)))

    @helpers.skipIfNoService(['compute.instances', 'compute.images',
                              'compute.vm_types', 'storage.volumes'])
    def test_block_device_mapping_attachments(self):
        label = "cb-blkattch-{0}".format(helpers.get_uuid())

        if self.provider.PROVIDER_ID == ProviderList.OPENSTACK:
            raise self.skipTest("Not running BDM tests because OpenStack is"
                                " not stable enough yet")

        test_vol = self.provider.storage.volumes.create(
           label, 1,
           helpers.get_provider_test_data(self.provider,
                                          "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            test_snap = test_vol.create_snapshot(label=label,
                                                 description=label)

            def cleanup_snap(snap):
                if snap:
                    snap.delete()
                    snap.wait_for([SnapshotState.UNKNOWN],
                                  terminal_states=[SnapshotState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
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
                vm_type_name = helpers.get_provider_test_data(
                    self.provider,
                    "vm_type")
                vm_type = self.provider.compute.vm_types.find(
                    name=vm_type_name)[0]
                for _ in range(vm_type.num_ephemeral_disks):
                    lc.add_ephemeral_device()

                subnet = helpers.get_or_create_default_subnet(
                    self.provider)

                inst = helpers.create_test_instance(
                    self.provider,
                    label,
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
                              'security.vm_firewalls'])
    def test_instance_methods(self):
        label = "cb-instmethods-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        test_inst = None
        fw = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                instance=test_inst, vm_firewall=fw, network=net)):
            net = self.provider.networking.networks.create(
                label=label, cidr_block='10.0.0.0/16')
            cidr = '10.0.1.0/24'
            subnet = net.create_subnet(label=label, cidr_block=cidr,
                                       zone=helpers.get_provider_test_data(
                                                    self.provider,
                                                    'placement'))
            test_inst = helpers.get_test_instance(self.provider, label,
                                                  subnet=subnet)
            fw = self.provider.security.vm_firewalls.create(
                label=label, description=label, network_id=net.id)

            # Check adding a VM firewall to a running instance
            test_inst.add_vm_firewall(fw)
            test_inst.refresh()
            self.assertTrue(
                fw in test_inst.vm_firewalls, "Expected VM firewall '%s'"
                " to be among instance vm_firewalls: [%s]" %
                (fw, test_inst.vm_firewalls))

            # Check removing a VM firewall from a running instance
            test_inst.remove_vm_firewall(fw)
            test_inst.refresh()
            self.assertTrue(
                fw not in test_inst.vm_firewalls, "Expected VM firewall"
                " '%s' to be removed from instance vm_firewalls: [%s]" %
                (fw, test_inst.vm_firewalls))

            # check floating ips
            router = self.provider.networking.routers.create(label, net)
            gateway = net.gateways.get_or_create_inet_gateway()

            def cleanup_router(router, gateway):
                with helpers.cleanup_action(lambda: router.delete()):
                    with helpers.cleanup_action(lambda: gateway.delete()):
                        router.detach_subnet(subnet)
                        router.detach_gateway(gateway)

            with helpers.cleanup_action(lambda: cleanup_router(router,
                                                               gateway)):
                router.attach_subnet(subnet)
                router.attach_gateway(gateway)
                # check whether adding an elastic ip works
                fip = gateway.floating_ips.create()
                self.assertFalse(
                    fip.in_use,
                    "Newly created floating IP address should not be in use.")

                with helpers.cleanup_action(lambda: fip.delete()):
                    with helpers.cleanup_action(
                            lambda: test_inst.remove_floating_ip(fip)):
                        test_inst.add_floating_ip(fip)
                        test_inst.refresh()
                        # On Devstack, FloatingIP is listed under private_ips.
                        self.assertIn(fip.public_ip, test_inst.public_ips +
                                      test_inst.private_ips)
                        fip.refresh()
                        self.assertTrue(
                            fip.in_use,
                            "Attached floating IP address should be in use.")
                    test_inst.refresh()
                    test_inst.reboot()
                    test_inst.wait_till_ready()
                    self.assertNotIn(
                        fip.public_ip,
                        test_inst.public_ips + test_inst.private_ips)
