import time
import uuid

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.factory import ProviderList
from cloudbridge.cloud.interfaces import SnapshotState
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.provider import TestMockHelperMixin
from cloudbridge.cloud.interfaces.resources import AttachmentInfo
from cloudbridge.cloud.interfaces.resources import Snapshot
from cloudbridge.cloud.interfaces.resources import Volume

import six


class CloudBlockStoreServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['storage.volumes'])
    def test_crud_volume(self):
        """
        Create a new volume, check whether the expected values are set,
        and delete it
        """
        def create_vol(name):
            return self.provider.storage.volumes.create(
                name,
                1,
                helpers.get_provider_test_data(self.provider, "placement"))

        def cleanup_vol(vol):
            vol.delete()
            vol.wait_for([VolumeState.DELETED, VolumeState.UNKNOWN],
                         terminal_states=[VolumeState.ERROR])

        sit.check_crud(self, self.provider.storage.volumes, Volume,
                       "cb_createvol", create_vol, cleanup_vol)

    @helpers.skipIfNoService(['storage.volumes'])
    def test_attach_detach_volume(self):
        """
        Create a new volume, and attempt to attach it to an instance
        """
        name = "cb_attachvol-{0}".format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        test_instance = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, name)
            test_instance = helpers.get_test_instance(
                self.provider, name, subnet=subnet)

            test_vol = self.provider.storage.volumes.create(
                name, 1, test_instance.zone_id)
            with helpers.cleanup_action(lambda: test_vol.delete()):
                test_vol.wait_till_ready()
                test_vol.attach(test_instance, '/dev/sda2')
                test_vol.wait_for(
                    [VolumeState.IN_USE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
                test_vol.detach()
                test_vol.wait_for(
                    [VolumeState.AVAILABLE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])

    @helpers.skipIfNoService(['storage.volumes'])
    def test_volume_properties(self):
        """
        Test volume properties
        """
        name = "cb_volprops-{0}".format(helpers.get_uuid())
        vol_desc = 'newvoldesc1'
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        net = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, name)
            test_instance = helpers.get_test_instance(
                self.provider, name, subnet=subnet)

            test_vol = self.provider.storage.volumes.create(
                name, 1, test_instance.zone_id, description=vol_desc)
            with helpers.cleanup_action(lambda: test_vol.delete()):
                test_vol.wait_till_ready()
                self.assertTrue(
                    isinstance(test_vol.size, six.integer_types) and
                    test_vol.size >= 0,
                    "Volume.size must be a positive number, but got %s"
                    % test_vol.size)
                self.assertTrue(
                    test_vol.description is None or
                    isinstance(test_vol.description, six.string_types),
                    "Volume.description must be None or a string. Got: %s"
                    % test_vol.description)
                self.assertIsNone(test_vol.source)
                self.assertIsNone(test_vol.source)
                self.assertIsNotNone(test_vol.create_time)
                self.assertIsNotNone(test_vol.zone_id)
                self.assertIsNone(test_vol.attachments)
                test_vol.attach(test_instance, '/dev/sda2')
                test_vol.wait_for(
                    [VolumeState.IN_USE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
                self.assertIsNotNone(test_vol.attachments)
                self.assertIsInstance(test_vol.attachments, AttachmentInfo)
                self.assertEqual(test_vol.attachments.volume, test_vol)
                self.assertEqual(test_vol.attachments.instance_id,
                                 test_instance.id)
                self.assertEqual(test_vol.attachments.device,
                                 "/dev/sda2")
                test_vol.detach()
                test_vol.name = 'newvolname1'
                test_vol.wait_for(
                    [VolumeState.AVAILABLE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
                self.assertEqual(test_vol.name, 'newvolname1')
                self.assertEqual(test_vol.description, vol_desc)
                self.assertIsNone(test_vol.attachments)
                test_vol.wait_for(
                    [VolumeState.AVAILABLE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])

    @helpers.skipIfNoService(['storage.snapshots'])
    def test_crud_snapshot(self):
        """
        Create a new volume, create a snapshot of the volume, and check
        whether list_snapshots properly detects the new snapshot.
        Delete everything afterwards.
        """
        name = "cb_crudsnap-{0}".format(helpers.get_uuid())
        test_vol = self.provider.storage.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()

            def create_snap(name):
                return test_vol.create_snapshot(name=name,
                                                description=name)

            def cleanup_snap(snap):
                snap.delete()
                snap.wait_for(
                    [SnapshotState.UNKNOWN],
                    terminal_states=[SnapshotState.ERROR])

            sit.check_crud(self, self.provider.storage.snapshots, Snapshot,
                           "cb_snap", create_snap, cleanup_snap)

            # Test creation of a snap via SnapshotService
            def create_snap2(name):
                return self.provider.storage.snapshots.create(
                    name=name, volume=test_vol, description=name)

            if (self.provider.PROVIDER_ID == ProviderList.AWS and
                    not isinstance(self.provider, TestMockHelperMixin)):
                time.sleep(15)  # Or get SnapshotCreationPerVolumeRateExceeded
            sit.check_crud(self, self.provider.storage.snapshots, Snapshot,
                           "cb_snaptwo", create_snap2, cleanup_snap)

    @helpers.skipIfNoService(['storage.snapshots'])
    def test_snapshot_properties(self):
        """
        Test snapshot properties
        """
        name = "cb_snapprop-{0}".format(uuid.uuid4())
        test_vol = self.provider.storage.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            snap_name = "cb_snap-{0}".format(name)
            test_snap = test_vol.create_snapshot(name=snap_name,
                                                 description=snap_name)

            def cleanup_snap(snap):
                snap.delete()
                snap.wait_for(
                    [SnapshotState.UNKNOWN],
                    terminal_states=[SnapshotState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
                test_snap.wait_till_ready()
                self.assertTrue(isinstance(test_vol.size, six.integer_types))
                self.assertEqual(
                    test_snap.size, test_vol.size,
                    "Snapshot.size must match original volume's size: %s"
                    " but is: %s" % (test_vol.size, test_snap.size))
                self.assertTrue(
                    test_vol.description is None or
                    isinstance(test_vol.description, six.string_types),
                    "Snapshot.description must be None or a string. Got: %s"
                    % test_vol.description)
                self.assertEqual(test_vol.id, test_snap.volume_id)
                self.assertIsNotNone(test_vol.create_time)
                test_snap.name = 'snapnewname1'
                test_snap.description = 'snapnewdescription1'
                test_snap.refresh()
                self.assertEqual(test_snap.name, 'snapnewname1')
                self.assertEqual(test_snap.description, 'snapnewdescription1')

                # Test volume creation from a snapshot (via VolumeService)
                sv_name = "cb_snapvol_{0}".format(test_snap.name)
                snap_vol = self.provider.storage.volumes.create(
                    sv_name,
                    1,
                    helpers.get_provider_test_data(self.provider, "placement"),
                    snapshot=test_snap)
                with helpers.cleanup_action(lambda: snap_vol.delete()):
                    snap_vol.wait_till_ready()

                # Test volume creation from a snapshot (via Snapshot)
                snap_vol2 = test_snap.create_volume(
                    helpers.get_provider_test_data(self.provider, "placement"))
                with helpers.cleanup_action(lambda: snap_vol2.delete()):
                    snap_vol2.wait_till_ready()
