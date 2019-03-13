import time

import six

from cloudbridge.base import helpers as cb_helpers
from cloudbridge.factory import ProviderList
from cloudbridge.interfaces import SnapshotState
from cloudbridge.interfaces import VolumeState
from cloudbridge.interfaces.provider import TestMockHelperMixin
from cloudbridge.interfaces.resources import AttachmentInfo
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import Volume

from tests import helpers
from tests.helpers import ProviderTestBase
from tests.helpers import standard_interface_tests as sit


class CloudBlockStoreServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['storage.volumes', 'storage.volumes'])
    def test_storage_services_event_pattern(self):
        # pylint:disable=protected-access
        self.assertEqual(
            self.provider.storage.volumes._service_event_pattern,
            "provider.storage.volumes",
            "Event pattern for {} service should be '{}', "
            "but found '{}'.".format("volumes",
                                     "provider.storage.volumes",
                                     self.provider.storage.volumes.
                                     _service_event_pattern))
        # pylint:disable=protected-access
        self.assertEqual(
            self.provider.storage.snapshots._service_event_pattern,
            "provider.storage.snapshots",
            "Event pattern for {} service should be '{}', "
            "but found '{}'.".format("snapshots",
                                     "provider.storage.snapshots",
                                     self.provider.storage.snapshots.
                                     _service_event_pattern))

    @helpers.skipIfNoService(['storage.volumes'])
    def test_crud_volume(self):
        def create_vol(label):
            return self.provider.storage.volumes.create(
                label, 1)

        def cleanup_vol(vol):
            if vol:
                vol.delete()
                vol.wait_for([VolumeState.DELETED, VolumeState.UNKNOWN],
                             terminal_states=[VolumeState.ERROR])
                vol.refresh()
                self.assertTrue(
                    vol.state == VolumeState.UNKNOWN,
                    "Volume.state must be unknown when refreshing after a "
                    "delete but got %s"
                    % vol.state)

        sit.check_crud(self, self.provider.storage.volumes, Volume,
                       "cb-createvol", create_vol, cleanup_vol)

    @helpers.skipIfNoService(['storage.volumes'])
    def test_attach_detach_volume(self):
        label = "cb-attachvol-{0}".format(helpers.get_uuid())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        with cb_helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance)):
            subnet = helpers.get_or_create_default_subnet(
                self.provider)
            test_instance = helpers.get_test_instance(
                self.provider, label, subnet=subnet)

            test_vol = self.provider.storage.volumes.create(
                label, 1)
            with cb_helpers.cleanup_action(lambda: test_vol.delete()):
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
        label = "cb-volprops-{0}".format(helpers.get_uuid())
        vol_desc = 'newvoldesc1'
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        with cb_helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance)):
            subnet = helpers.get_or_create_default_subnet(
                self.provider)
            test_instance = helpers.get_test_instance(
                self.provider, label, subnet=subnet)

            test_vol = self.provider.storage.volumes.create(
                label, 1, description=vol_desc)
            with cb_helpers.cleanup_action(lambda: test_vol.delete()):
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
                if (self.provider.PROVIDER_ID != 'azure' and
                        self.provider.PROVIDER_ID != 'gcp'):
                    self.assertEqual(test_vol.attachments.device,
                                     "/dev/sda2")
                test_vol.detach()
                test_vol.label = 'newvolname1'
                test_vol.wait_for(
                    [VolumeState.AVAILABLE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
                self.assertEqual(test_vol.label, 'newvolname1')
                self.assertEqual(test_vol.description, vol_desc)
                self.assertIsNone(test_vol.attachments)
                test_vol.wait_for(
                    [VolumeState.AVAILABLE],
                    terminal_states=[VolumeState.ERROR, VolumeState.DELETED])

    @helpers.skipIfNoService(['storage.snapshots'])
    def test_crud_snapshot(self):
        # Create a new volume, create a snapshot of the volume, and check
        # whether list_snapshots properly detects the new snapshot.
        # Delete everything afterwards.
        label = "cb-crudsnap-{0}".format(helpers.get_uuid())
        test_vol = self.provider.storage.volumes.create(
            label, 1)
        with cb_helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()

            def create_snap(label):
                return test_vol.create_snapshot(label=label,
                                                description=label)

            def cleanup_snap(snap):
                if snap:
                    snap.delete()
                    snap.wait_for([SnapshotState.UNKNOWN],
                                  terminal_states=[SnapshotState.ERROR])
                    snap.refresh()
                    self.assertTrue(
                        snap.state == SnapshotState.UNKNOWN,
                        "Snapshot.state must be unknown when refreshing after "
                        "a delete but got %s"
                        % snap.state)

            sit.check_crud(self, self.provider.storage.snapshots, Snapshot,
                           "cb-snap", create_snap, cleanup_snap)

            # Test creation of a snap via SnapshotService
            def create_snap2(label):
                return self.provider.storage.snapshots.create(
                    label=label, volume=test_vol, description=label)

            if (self.provider.PROVIDER_ID == ProviderList.AWS and
                    not isinstance(self.provider, TestMockHelperMixin)):
                time.sleep(15)  # Or get SnapshotCreationPerVolumeRateExceeded
            sit.check_crud(self, self.provider.storage.snapshots, Snapshot,
                           "cb-snaptwo", create_snap2, cleanup_snap)

    @helpers.skipIfNoService(['storage.snapshots'])
    def test_snapshot_properties(self):
        label = "cb-snapprop-{0}".format(helpers.get_uuid())
        test_vol = self.provider.storage.volumes.create(
            label, 1)
        with cb_helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            snap_label = "cb-snap-{0}".format(label)
            test_snap = test_vol.create_snapshot(label=snap_label,
                                                 description=snap_label)

            def cleanup_snap(snap):
                if snap:
                    snap.delete()
                    snap.wait_for([SnapshotState.UNKNOWN],
                                  terminal_states=[SnapshotState.ERROR])

            with cb_helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
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
                test_snap.label = 'snapnewname1'
                test_snap.description = 'snapnewdescription1'
                test_snap.refresh()
                self.assertEqual(test_snap.label, 'snapnewname1')
                self.assertEqual(test_snap.description, 'snapnewdescription1')

                # Test volume creation from a snapshot (via VolumeService)
                sv_label = "cb-snapvol-{0}".format(test_snap.name)
                snap_vol = self.provider.storage.volumes.create(
                    sv_label, 1, snapshot=test_snap)
                with cb_helpers.cleanup_action(lambda: snap_vol.delete()):
                    snap_vol.wait_till_ready()

                # Test volume creation from a snapshot (via Snapshot)
                snap_vol2 = test_snap.create_volume()
                with cb_helpers.cleanup_action(lambda: snap_vol2.delete()):
                    snap_vol2.wait_till_ready()
