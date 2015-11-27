import uuid

from cloudbridge.cloud.interfaces import SnapshotState
from cloudbridge.cloud.interfaces import VolumeState
from test.helpers import ProviderTestBase
import test.helpers as helpers


class CloudBlockStoreServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudBlockStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

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
            find_volumes = self.provider.block_store.volumes.find(name=name)
            self.assertTrue(
                len(find_volumes) == 1,
                "Find volumes does not return the expected volume %s" %
                name)

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

    def test_attach_detach_volume(self):
        """
        Create a new volume, and attempt to attach it to an instance
        """
        instance_name = "CBVolOps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        test_instance = helpers.get_test_instance(self.provider, instance_name)
        with helpers.cleanup_action(lambda: test_instance.terminate()):
            name = "CBUnitTestAttachVol-{0}".format(uuid.uuid4())
            test_vol = self.provider.block_store.volumes.create(
                name, 1, test_instance.placement_zone)
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
                find_snap = self.provider.block_store.snapshots.find(name=name)
                self.assertTrue(
                    len(find_snap) == 1,
                    "Find snaps does not return the expected snapshot %s" %
                    name)

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
            snaps = self.provider.block_store.snapshots.list()
            found_snaps = [snap for snap in snaps
                           if snap.name == snap_name]
            self.assertTrue(
                len(found_snaps) == 0,
                "Snapshot %s should have been deleted but still exists." %
                snap_name)
