import uuid

import ipaddress

from cloudbridge.cloud.interfaces \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces import InstanceState
from cloudbridge.cloud.interfaces.resources import InstanceType
from cloudbridge.cloud.interfaces.resources import WaitStateException
from test.helpers import ProviderTestBase
import test.helpers as helpers


class CloudComputeServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudComputeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_instance(self):
        name = "CBInstCrud-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        inst = helpers.create_test_instance(self.provider, name)

        def cleanup_inst(instance):
            instance.terminate()
            instance.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())

        with helpers.cleanup_action(lambda: cleanup_inst(inst)):
            inst.wait_till_ready(interval=self.get_test_wait_interval())

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

    def test_instance_properties(self):
        name = "CBInstProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        kp = self.provider.security.key_pairs.create(name=name)
        sg = self.provider.security.security_groups.create(
            name=name, description=name)

        test_instance = helpers.get_test_instance(self.provider,
                                                  name, keypair=kp,
                                                  security_groups=[sg])

        def cleanup(inst, kp, sg):
            inst.terminate()
            inst.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())
            kp.delete()
            sg.delete()

        with helpers.cleanup_action(lambda: cleanup(test_instance, kp, sg)):
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
            self.assertIsInstance(test_instance.public_ips, list)
            self.assertIsInstance(test_instance.private_ips, list)
            self.assertEqual(
                test_instance.key_pair_name,
                kp.name)
            self.assertIsInstance(test_instance.security_groups, list)
            self.assertEqual(
                test_instance.security_groups[0],
                sg)
            # Must have either a public or a private ip
            ip_private = test_instance.private_ips[0] \
                if test_instance.private_ips else None
            ip_address = test_instance.public_ips[0] \
                if test_instance.public_ips else ip_private
            self.assertIsNotNone(
                ip_address,
                "Instance must have either a public IP or a private IP")
            self.assertTrue(
                self._is_valid_ip(ip_address),
                "Instance must have a valid IP address")
            self.assertIsInstance(test_instance.instance_type, InstanceType)

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
        lc.add_volume_device(
            is_root=True,
            source=img,
            # TODO: This should be greater than the ami size or tests will fail
            # on actual infrastructure. Needs an image.size method
            size=2,
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

    def test_block_device_mapping_attachments(self):
        name = "CBInstBlkAttch-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

#         test_vol = self.provider.block_store.volumes.create(
#             name,
#             1,
#             helpers.get_provider_test_data(self.provider, "placement"))
#         with helpers.cleanup_action(lambda: test_vol.delete()):
#             test_vol.wait_till_ready(interval=self.get_test_wait_interval())
#             test_snap = test_vol.create_snapshot(name=name,
#                                                  description=name)
#
#             def cleanup_snap(snap):
#                 snap.delete()
#                 snap.wait_for(
#                     [SnapshotState.UNKNOWN],
#                     terminal_states=[SnapshotState.ERROR],
#                     interval=self.get_test_wait_interval())
#
#             with helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
#                 test_snap.wait_till_ready(
#                     interval=self.get_test_wait_interval())

        lc = self.provider.compute.instances.create_launch_config()

        # Add a new blank volume
        lc.add_volume_device(size=1, delete_on_terminate=True)

        # Attach an existing volume
#                 lc.add_volume_device(size=1, source=test_vol,
#                                      delete_on_terminate=True)

        # Add a new volume based on a snapshot
#                 lc.add_volume_device(size=1, source=test_snap,
#                                      delete_on_terminate=True)

        # Override root volume size
        image_id = helpers.get_provider_test_data(
            self.provider,
            "image")
        img = self.provider.compute.images.get(image_id)
        lc.add_volume_device(
            is_root=True,
            source=img,
            # TODO: This should be greater than the ami size or tests
            # will fail on actual infrastructure. Needs an image.size
            # method
            size=2,
            delete_on_terminate=True)

        # Add all available ephemeral devices
        instance_type_name = helpers.get_provider_test_data(
            self.provider,
            "instance_type")
        inst_type = self.provider.compute.instance_types.find(
            name=instance_type_name)[0]
        for _ in range(inst_type.num_ephemeral_disks):
            lc.add_ephemeral_device()

        inst = helpers.create_test_instance(
            self.provider,
            name,
            zone=helpers.get_provider_test_data(
                self.provider,
                'placement'),
            launch_config=lc)

        def cleanup(instance):
            instance.terminate()
            instance.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())
        with helpers.cleanup_action(lambda: cleanup(inst)):
            try:
                inst.wait_till_ready(
                    interval=self.get_test_wait_interval())
            except WaitStateException as e:
                self.fail("The block device mapped launch did not "
                          " complete successfully: %s" % e)
            # TODO: Check instance attachments and make sure they
            # correspond to requested mappings
