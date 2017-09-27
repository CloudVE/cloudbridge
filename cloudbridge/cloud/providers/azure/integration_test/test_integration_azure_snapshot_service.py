import uuid

from cloudbridge.cloud.providers.azure.integration_test import helpers


class AzureIntegrationSnapshotServiceTestCase(helpers.ProviderTestBase):
    @helpers.skipIfNoService(['block_store'])
    def test_azure_snapshot_service(self):
        snapshot_name = '{0}'.format(uuid.uuid4().hex[:6])
        volume_name = '{0}'.format(uuid.uuid4().hex[:6])

        snapshot_list_before_create = \
            self.provider.block_store.snapshots.list()
        print(str(len(snapshot_list_before_create)))

        vol = self.provider.block_store.volumes.create(volume_name, 1)
        vol.wait_till_ready()

        self.assertTrue(vol is not None, 'Volume not created')

        snapshot = self.provider.block_store. \
            snapshots.create(snapshot_name, vol)
        snapshot.wait_till_ready()
        self.assertTrue(snapshot is not None, 'Snapshot not created')

        snapshot_id = snapshot.id

        snapshot_list_after_create = \
            self.provider.block_store.snapshots.list()
        print(str(len(snapshot_list_after_create)))

        self.assertTrue(len(snapshot_list_after_create),
                        len(snapshot_list_before_create) + 1)

        snapshot = self.provider.block_store.snapshots.get(snapshot_id)
        print("Get Snapshot  - " + str(snapshot))
        self.assertTrue(
            snapshot.name == snapshot_name,
            "Snapshot name should be MySnapshot")

        snapshot_find = self.provider.block_store. \
            snapshots.find(snapshot_name)
        print("Find Snapshot  - " + str(snapshot))
        self.assertEqual(
            len(snapshot_find), 1)

        volume = snapshot.create_volume()
        volume.wait_till_ready()
        self.assertTrue(volume is not None, 'Volume not created')

        snapshot.refresh()
        self.assertTrue(snapshot.id == snapshot_id,
                        'Snapshot id should match on refresh')

        snapshot_list_before_delete = \
            self.provider.block_store.snapshots.list()
        print(str(len(snapshot_list_before_delete)))

        snapshot.delete()

        snapshot_list_after_delete = \
            self.provider.block_store.snapshots.list()
        print(str(len(snapshot_list_after_delete)))

        self.assertEqual(len(snapshot_list_after_delete),
                         len(snapshot_list_before_delete) - 1)

        volume.delete()
        vol.delete()
