import ipaddress
import uuid

from test import helpers
from test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces import InvalidConfigurationException
from cloudbridge.cloud.interfaces import TestMockHelperMixin
from cloudbridge.cloud.interfaces.exceptions import WaitStateException
from cloudbridge.cloud.interfaces.resources import InstanceType
# from cloudbridge.cloud.interfaces.resources import SnapshotState

import six


class CloudComputeServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['compute.instances', 'network'])
    def test_crud_instance(self):
        name = "CBInstCrud-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        inst = None
        net = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                inst, net)):
            net, subnet = helpers.create_test_network(self.provider, name)
            inst = helpers.get_test_instance(self.provider, name,
                                             subnet=subnet)

            all_instances = self.provider.compute.instances.list()

            list_instances = [i for i in all_instances if i.name == name]
            self.assertTrue(
                len(list_instances) == 1,
                "List instances does not return the expected instance %s" %
                name)

            # check iteration
            iter_instances = [i for i in self.provider.compute.instances
                              if i.name == name]
            self.assertTrue(
                len(iter_instances) == 1,
                "Iter instances does not return the expected instance %s" %
                name)

            # check find
            find_instances = self.provider.compute.instances.find(name=name)
            self.assertTrue(
                len(find_instances) == 1,
                "Find instances does not return the expected instance %s" %
                name)

            # check non-existent find
            find_instances = self.provider.compute.instances.find(
                name="non_existent")
            self.assertTrue(
                len(find_instances) == 0,
                "Find() for a non-existent image returned %s" % find_instances)

            get_inst = self.provider.compute.instances.get(
                inst.id)
            self.assertTrue(
                list_instances[0] ==
                get_inst == inst,
                "Objects returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(list_instances[0].id,
                                         get_inst.id,
                                         inst.id))
            self.assertTrue(
                list_instances[0].name ==
                get_inst.name == inst.name,
                "Names returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(list_instances[0].name,
                                         get_inst.name,
                                         inst.name))
        deleted_inst = self.provider.compute.instances.get(
            inst.id)
        self.assertTrue(
            deleted_inst is None or deleted_inst.state in (
                InstanceState.TERMINATED,
                InstanceState.UNKNOWN),
            "Instance %s should have been deleted but still exists." %
            name)

    def _is_valid_ip(self, address):
        try:
            ipaddress.ip_address(address)
        except ValueError:
            return False
        return True

    @helpers.skipIfNoService(['compute.instances', 'network',
                              'security.security_groups',
                              'security.key_pairs'])
    def test_instance_properties(self):
        name = "CBInstProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

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

            self.assertTrue(
                test_instance.id in repr(test_instance),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")
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
            # FIXME: Moto is not returning the instance's placement zone
#             find_zone = [zone for zone in
#                          self.provider.compute.regions.current.zones
#                          if zone.id == test_instance.zone_id]
#             self.assertEqual(len(find_zone), 1,
#                              "Instance's placement zone could not be "
#                              " found in zones list")
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
            size=img.min_disk if img and img.min_disk else 2,
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
        name = "CBInstBlkAttch-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

        # Comment out BDM tests because OpenStack is not stable enough yet
        if True:
            if True:

                # test_vol = self.provider.block_store.volumes.create(
                #    name,
                #    1,
                #    helpers.get_provider_test_data(self.provider,
                #                                   "placement"))
                # with helpers.cleanup_action(lambda: test_vol.delete()):
                #    test_vol.wait_till_ready()
                #    test_snap = test_vol.create_snapshot(name=name,
                #                                         description=name)
                #
                #    def cleanup_snap(snap):
                #        snap.delete()
                #        snap.wait_for(
                #            [SnapshotState.UNKNOWN],
                #            terminal_states=[SnapshotState.ERROR])
                #
                #    with helpers.cleanup_action(lambda:
                #                                cleanup_snap(test_snap)):
                #         test_snap.wait_till_ready()

                lc = self.provider.compute.instances.create_launch_config()

#                 # Add a new blank volume
#                 lc.add_volume_device(size=1, delete_on_terminate=True)
#
#                 # Attach an existing volume
#                 lc.add_volume_device(size=1, source=test_vol,
#                                      delete_on_terminate=True)
#
#                 # Add a new volume based on a snapshot
#                 lc.add_volume_device(size=1, source=test_snap,
#                                      delete_on_terminate=True)

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
                    size=img.min_disk if img and img.min_disk else 2,
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

    @helpers.skipIfNoService(['compute.instances', 'network',
                              'security.security_groups'])
    def test_instance_methods(self):
        name = "CBInstProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

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
            router = self.provider.network.create_router(name=name)

            with helpers.cleanup_action(lambda: router.delete()):

                # TODO: Cloud specific code, needs fixing
                if self.provider.PROVIDER_ID == 'openstack':
                    for n in self.provider.network.list():
                        if n.external:
                            external_net = n
                            break
                else:
                    external_net = net
                router.attach_network(external_net.id)
                router.add_route(subnet.id)

                def cleanup_router():
                    router.remove_route(subnet.id)
                    router.detach_network()

                with helpers.cleanup_action(lambda: cleanup_router()):
                    # check whether adding an elastic ip works
                    fip = self.provider.network.create_floating_ip()
                    with helpers.cleanup_action(lambda: fip.delete()):
                        test_inst.add_floating_ip(fip.public_ip)
                        test_inst.refresh()
                        self.assertIn(fip.public_ip, test_inst.public_ips)

                        if isinstance(self.provider, TestMockHelperMixin):
                            # TODO: Moto bug does not refresh removed public ip
                            return

                        # check whether removing an elastic ip works
                        test_inst.remove_floating_ip(fip.public_ip)
                        test_inst.refresh()
                        self.assertNotIn(fip.public_ip, test_inst.public_ips)
