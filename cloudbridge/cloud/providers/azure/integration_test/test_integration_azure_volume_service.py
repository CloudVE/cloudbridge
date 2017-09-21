import uuid

from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.providers.azure.integration_test import helpers


class AzureIntegrationVolumeServiceTestCase(helpers.ProviderTestBase):
    @helpers.skipIfNoService(['block_store'])
    def test_azure_volume_service(self):
        volume_name = '{0}'.format(uuid.uuid4().hex[:6])
        snapshot_name = '{0}'.format(uuid.uuid4().hex[:6])
        instance_id = 'TEST-INST'

        volume_list_before_create = self.provider.block_store.volumes.list()
        print(str(len(volume_list_before_create)))

        volume = self.provider.block_store.volumes.create(volume_name, 1)
        volume.wait_till_ready()
        self.assertTrue(volume is not None, 'Volume not created')
        volume_id = volume.id

        volume_list_after_create = self.provider.block_store.volumes.list()
        print(str(len(volume_list_after_create)))

        self.assertTrue(
            len(volume_list_after_create), len(volume_list_before_create) + 1)

        volume = self.provider.block_store.volumes.get(volume_id)
        print("Get Volume  - " + str(volume))
        self.assertTrue(
            volume.name == volume_name, "Volume name should be MyVolume")

        volume_find = self.provider.block_store.volumes.find(volume_name)
        print("Find Volume  - " + str(volume))
        self.assertEqual(
            len(volume_find), 1)

        volume.attach(instance_id)
        volume.wait_for(
            [VolumeState.IN_USE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
        self.assertTrue(volume.state == VolumeState.IN_USE)

        volume.detach()
        volume.wait_for(
            [VolumeState.AVAILABLE],
            terminal_states=[VolumeState.ERROR, VolumeState.DELETED])
        self.assertTrue(volume.state == VolumeState.AVAILABLE)

        snapshot = volume.create_snapshot(snapshot_name)
        self.assertTrue(snapshot is not None,
                        'Snapshot {0} not created'.format(snapshot_name))

        snapshot.delete()

        volume.refresh()
        self.assertTrue(volume.id == volume_id,
                        'Volume id should match on refresh')

        volume_list_before_delete = self.provider.block_store.volumes.list()
        print(str(len(volume_list_before_delete)))

        volume.delete()

        volume_list_after_delete = self.provider.block_store.volumes.list()
        print(str(len(volume_list_after_delete)))
        self.assertTrue(len(volume_list_after_delete),
                        len(volume_list_before_delete) - 1)
