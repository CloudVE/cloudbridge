import itertools
import uuid

import ipaddress

from cloudbridge.cloud.interfaces \
    import InvalidConfigurationException
from cloudbridge.cloud.interfaces import InstanceState
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

            # check iteration
            iter_instances = list(itertools.islice(
                self.provider.compute.instances,
                len(all_instances)))
            self.assertListEqual(iter_instances, all_instances)

            found_instances = [i for i in all_instances if i.name == name]
            self.assertTrue(
                len(found_instances) == 1,
                "List instances does not return the expected instance %s" %
                name)

            get_inst = self.provider.compute.instances.get(
                inst.id)
            self.assertTrue(
                found_instances[0].id ==
                get_inst.id == inst.id,
                "Ids returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(found_instances[0].id,
                                         get_inst.id,
                                         inst.id))
            self.assertTrue(
                found_instances[0].name ==
                get_inst.name == inst.name,
                "Names returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(found_instances[0].name,
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
        instance_name = "CBInstProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        test_instance = helpers.get_test_instance(self.provider,
                                                  instance_name)
        with helpers.cleanup_action(lambda: test_instance.terminate()):
            self.assertTrue(
                test_instance.id in repr(test_instance),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")
            self.assertEqual(
                test_instance.name, instance_name,
                "Instance name {0} is not equal to the expected name"
                " {1}".format(test_instance.name, instance_name))
            image_id = helpers.get_provider_test_data(self.provider, "image")
            self.assertEqual(test_instance.image_id, image_id,
                             "Image id {0} is not equal to the expected id"
                             " {1}".format(test_instance.image_id, image_id))
            self.assertIsInstance(test_instance.public_ips, list)
            self.assertIsInstance(test_instance.private_ips, list)
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

    def test_block_device_mappings(self):
        name = "CBInstBlkMap-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

        lc = self.provider.compute.instances.create_launch_config()

        # specifying an invalid size should raise
        # an exception
        with self.assertRaises(InvalidConfigurationException):
            lc.add_volume_device(-1)

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

        # Add all available ephemeral devices
        instance_type_name = helpers.get_provider_test_data(
            self.provider,
            "instance_type")
        inst_type = next(self.provider.compute.instance_types.find(
            name=instance_type_name))
        for _ in range(inst_type.num_ephemeral_disks):
            lc.add_ephemeral_device()

        # block_devices should be populated
        self.assertTrue(
            len(lc.block_devices) == 2 + inst_type.num_ephemeral_disks,
            "Expected %d total block devices bit found %d" %
            (2 + inst_type.num_ephemeral_disks, len(lc.block_devices)))

        inst = helpers.create_test_instance(
            self.provider,
            name,
            zone=helpers.get_provider_test_data(self.provider, 'placement'),
            launch_config=lc)
        with helpers.cleanup_action(lambda: inst.terminate()):
            try:
                inst.wait_till_ready(
                    interval=self.get_test_wait_interval())
            except WaitStateException as e:
                self.fail("The block device mapped launch did not complete"
                          " successfully: %s" % e)
            inst.terminate()
            inst.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())
            # TODO: Check instance attachments and make sure they
            # correspond to requested mappings
