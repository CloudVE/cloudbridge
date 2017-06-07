import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces import SnapshotState


class AzureSnapshotsServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_create_and_get(self):
        volume_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
            '/resourceGroups/cloudbridge-azure'\
            '/providers/Microsoft.Compute/disks/Volume1"
        snapshot = self.provider.block_store. \
            snapshots.create("MySnapshot",
                             volume_id)
        snapshot.description = 'My snapshot'
        print("Create Snapshot - " + str(snapshot))
        self.assertTrue(
            snapshot.name == "MySnapshot",
            "Snapshot name should be MySnapshot")
        self.assertIsNotNone(snapshot.description)
        self.assertIsNotNone(snapshot.name)
        self.assertIsNotNone(snapshot.size)
        self.assertIsNotNone(snapshot.volume_id)
        self.assertIsNotNone(snapshot.create_time)
        snapshot.name = 'MySnapNewName'
        snapshot = self.provider.block_store.snapshots.get(snapshot.id)
        print("Get Snapshot  - " + str(snapshot))
        self.assertTrue(
            snapshot.name == "MySnapNewName",
            "Snapshot name should be MySnapshot")

        snapshot.delete()

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_delete(self):
        volume_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
            '/resourceGroups/cloudbridge-azure'\
            '/providers/Microsoft.Compute/disks/Volume1"
        snapshot = self.provider.block_store. \
            snapshots.create("MySnapshot",
                             volume_id, description='My snapshot')
        snapshot.refresh()
        print("Create Snapshot - " + str(snapshot))
        self.assertTrue(
            snapshot.name == "MySnapshot",
            "Snapshot name should be MySnapshot")
        snapshot.delete()

        delete_snapshot = snapshot.delete()
        self.assertEqual(delete_snapshot, False)

        snapshot.refresh()
        self.assertEqual(snapshot.state, SnapshotState.UNKNOWN)

        snapshot_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
                '/resourceGroups/cloudbridge-azure'\
                '/providers/Microsoft.Compute/snapshots/MySnapshot"
        snapshot1 = self.provider.block_store.snapshots.get(snapshot_id)
        self.assertTrue(
            snapshot1 is None, "Snapshot still exists")

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_create_volume(self):
        volume_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
            '/resourceGroups/cloudbridge-azure'\
            '/providers/Microsoft.Compute/disks/Volume1"
        snapshot = self.provider.block_store. \
            snapshots.create("MySnapshot",
                             volume_id,
                             description='My snapshot')
        self.assertTrue(
            snapshot.name == "MySnapshot",
            "Snapshot name should be MySnapshot")

        volume = snapshot.create_volume()
        self.assertTrue(
            volume is not None, "Snapshot not created")
        volume.delete()

        snapshot.delete()

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_get_ifNotExist(self):
        snapshot_id = "/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'\
                '/resourceGroups/cloudbridge-azure'\
                '/providers/Microsoft.Compute/snapshots/MySnapshot123"
        snapshot = self.provider.block_store.snapshots.get(snapshot_id)
        self.assertTrue(
            snapshot is None, "Snapshot should not be available")

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshots_list(self):
        snapshot_list = self.provider \
            .block_store.snapshots.list()
        print("Snapshot List - " + str(snapshot_list))
        self.assertTrue(
            snapshot_list.total_results > 0)

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_find_exists(self):
        snapshots = self.provider.block_store.snapshots.find("snapshot1")
        for snapshot in snapshots:
            self.assertTrue("snapshot" in snapshot.name)
        print(snapshots.total_results)
        self.assertTrue(snapshots.total_results > 0)

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_snapshot_find_not_exists(self):
        snapshots = self.provider.block_store.snapshots.find('dontfindme')
        self.assertTrue(snapshots.total_results == 0)
