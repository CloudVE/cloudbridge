import time
import uuid

from test import helpers
from test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces import SnapshotState
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.interfaces.resources import AttachmentInfo

import six


class CloudBlockStoreServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_crud_volume(self):
        """
        Create a new volume, check whether the expected values are set,
        and delete it
        """
        name = "CBUnitTestCreateVol-{0}".format(uuid.uuid4())
        test_vol = self.provider.block_store.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))

        def cleanup_vol(vol):
            vol.delete()
            vol.wait_for([VolumeState.DELETED, VolumeState.UNKNOWN],
                         terminal_states=[VolumeState.ERROR])

        with helpers.cleanup_action(lambda: cleanup_vol(test_vol)):
            test_vol.wait_till_ready()
            self.assertTrue(
                test_vol.id in repr(test_vol),
                "repr(obj) should contain the object id so that the object"
                " can be reconstructed, but does not. eval(repr(obj)) == obj")
            volumes = self.provider.block_store.volumes.list()
            list_volumes = [vol for vol in volumes if vol.name == name]
            self.assertTrue(
                len(list_volumes) == 1,
                "List volumes does not return the expected volume %s" %
                name)

            # check iteration
            iter_volumes = [vol for vol in self.provider.block_store.volumes
                            if vol.name == name]
            self.assertTrue(
                len(iter_volumes) == 1,
                "Iter volumes does not return the expected volume %s" %
                name)

            # check find
            find_vols = self.provider.block_store.volumes.find(name=name)
            self.assertTrue(
                len(find_vols) == 1,
                "Find volumes does not return the expected volume %s" %
                name)

            # check non-existent find
            # TODO: Moto has a bug with filters causing the following test
            # to fail. Need to add tag based filtering support for volumes
#             find_vols = self.provider.block_store.volumes.find(
#                 name="non_existent_vol")
#             self.assertTrue(
#                 len(find_vols) == 0,
#                 "Find() for a non-existent volume returned %s" % find_vols)

            get_vol = self.provider.block_store.volumes.get(
                test_vol.id)
            self.assertTrue(
                list_volumes[0] ==
                get_vol == test_vol,
                "Ids returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(list_volumes[0].id,
                                         get_vol.id,
                                         test_vol.id))
            self.assertTrue(
                list_volumes[0].name ==
                get_vol.name == test_vol.name,
                "Names returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(list_volumes[0].name,
                                         get_vol.name,
                                         test_vol.name))
        volumes = self.provider.block_store.volumes.list()
        found_volumes = [vol for vol in volumes if vol.name == name]
        self.assertTrue(
            len(found_volumes) == 0,
            "Volume %s should have been deleted but still exists." %
            name)

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_attach_detach_volume(self):
        """
        Create a new volume, and attempt to attach it to an instance
        """
        instance_name = "CBVolOps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        net = None
        test_instance = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, instance_name)
            test_instance = helpers.get_test_instance(
                self.provider, instance_name, subnet=subnet)
            name = "CBUnitTestAttachVol-{0}".format(uuid.uuid4())
            test_vol = self.provider.block_store.volumes.create(
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

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_volume_properties(self):
        """
        Test volume properties
        """
        instance_name = "CBVolProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        vol_desc = 'newvoldesc1'
        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        net = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, instance_name)
            test_instance = helpers.get_test_instance(
                self.provider, instance_name, subnet=subnet)

            name = "CBUnitTestVolProps-{0}".format(uuid.uuid4())
            test_vol = self.provider.block_store.volumes.create(
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

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_crud_snapshot(self):
        """
        Create a new volume, create a snapshot of the volume, and check
        whether list_snapshots properly detects the new snapshot.
        Delete everything afterwards.
        """
        name = "CBUnitTestCreateSnap-{0}".format(uuid.uuid4())
        test_vol = self.provider.block_store.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            snap_name = "CBSnapshot-{0}".format(name)
            test_snap = test_vol.create_snapshot(name=snap_name,
                                                 description=snap_name)

            def cleanup_snap(snap):
                snap.delete()
                snap.wait_for(
                    [SnapshotState.UNKNOWN],
                    terminal_states=[SnapshotState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_snap(test_snap)):
                test_snap.wait_till_ready()
                self.assertTrue(
                    test_snap.id in repr(test_snap),
                    "repr(obj) should contain the object id so that the object"
                    " can be reconstructed, but does not.")

                snaps = self.provider.block_store.snapshots.list()
                list_snaps = [snap for snap in snaps
                              if snap.name == snap_name]
                self.assertTrue(
                    len(list_snaps) == 1,
                    "List snapshots does not return the expected volume %s" %
                    name)

                # check iteration
                iter_snaps = [
                    snap for snap in self.provider.block_store.snapshots
                    if snap.name == snap_name]
                self.assertTrue(
                    len(iter_snaps) == 1,
                    "Iter snapshots does not return the expected volume %s" %
                    name)

                # check find
                find_snap = self.provider.block_store.snapshots.find(
                    name=snap_name)
                self.assertTrue(
                    len(find_snap) == 1,
                    "Find snaps does not return the expected snapshot %s" %
                    name)

                # check non-existent find
                # TODO: Moto has a bug with filters causing the following test
                # to fail. Need to add tag based filtering support for snaps
#                 find_snap = self.provider.block_store.snapshots.find(
#                     name="non_existent_snap")
#                 self.assertTrue(
#                     len(find_snap) == 0,
#                     "Find() for a non-existent snap returned %s" %
#                     find_snap)

                get_snap = self.provider.block_store.snapshots.get(
                    test_snap.id)
                self.assertTrue(
                    list_snaps[0] ==
                    get_snap == test_snap,
                    "Ids returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(list_snaps[0].id,
                                             get_snap.id,
                                             test_snap.id))
                self.assertTrue(
                    list_snaps[0].name ==
                    get_snap.name == test_snap.name,
                    "Names returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(list_snaps[0].name,
                                             get_snap.name,
                                             test_snap.name))

                # Test volume creation from a snapshot (via VolumeService)
                sv_name = "CBUnitTestSnapVol-{0}".format(name)
                snap_vol = self.provider.block_store.volumes.create(
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

            snaps = self.provider.block_store.snapshots.list()
            found_snaps = [snap for snap in snaps
                           if snap.name == snap_name]
            self.assertTrue(
                len(found_snaps) == 0,
                "Snapshot %s should have been deleted but still exists." %
                snap_name)

            # Test creation of a snap via SnapshotService
            snap_too_name = "CBSnapToo-{0}".format(name)
            time.sleep(15)  # Or get SnapshotCreationPerVolumeRateExceeded
            test_snap_too = self.provider.block_store.snapshots.create(
                name=snap_too_name, volume=test_vol, description=snap_too_name)
            with helpers.cleanup_action(lambda: cleanup_snap(test_snap_too)):
                test_snap_too.wait_till_ready()
                self.assertTrue(
                    test_snap_too.id in repr(test_snap_too),
                    "repr(obj) should contain the object id so that the object"
                    " can be reconstructed, but does not.")

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_snapshot_properties(self):
        """
        Test snapshot properties
        """
        name = "CBTestSnapProp-{0}".format(uuid.uuid4())
        test_vol = self.provider.block_store.volumes.create(
            name,
            1,
            helpers.get_provider_test_data(self.provider, "placement"))
        with helpers.cleanup_action(lambda: test_vol.delete()):
            test_vol.wait_till_ready()
            snap_name = "CBSnapProp-{0}".format(name)
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
