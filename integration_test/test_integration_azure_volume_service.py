import os
import tempfile
import uuid

import integration_test.helpers as helpers


class AzureIntegrationVolumeServiceTestCase(helpers.ProviderTestBase):

    def __init__(self, methodName, provider):
        super(AzureIntegrationVolumeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['block_store'])
    def test_azure_volume_service(self):
        volume_name = '{0}'.format(uuid.uuid4())
        snapshot_name = '{0}'.format(uuid.uuid4())

        volume_list_before_create = self.provider.block_store.volumes.list()
        print(str(len(volume_list_before_create)))

        volume = self.provider.block_store.volumes.create(volume_name, 1)
        volume.wait_till_ready()
        self.assertTrue(volume is not None, 'Volume not created')
        volume_id = volume.id

        volume_list_after_create = self.provider.block_store.volumes.list()
        print(str(len(volume_list_after_create)))

        self.assertTrue(len(volume_list_after_create), len(volume_list_before_create) + 1)

        volume = self.provider.block_store.volumes.get(volume_id)
        print("Get Volume  - " + str(volume))
        self.assertTrue(
            volume.name == volume_name, "Volume name should be MyVolume")

        volume_find = self.provider.block_store.volumes.find(volume_name)
        print("Find Volume  - " + str(volume))
        self.assertEqual(
            len(volume_find), 1)
        # volume.attach('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Compute/virtualMachines/ubuntu-intro2')
        # TODO: Add logic to verify that disk is attached to instance

        # volume.detach()
        # TODO: Add logic to verify that disk is not in use

        with self.assertRaises(NotImplementedError):
            snapshot = volume.create_snapshot(snapshot_name)
        # self.assertTrue(snapshot is not None, 'Snapshot {0} not created'.format(snapshot_name))

        volume.refresh()
        self.assertTrue(volume.id == volume_id, 'Volume id should match on refresh')

        volume_list_before_delete = self.provider.block_store.volumes.list()
        print(str(len(volume_list_before_delete)))

        volume.delete()

        volume_list_after_delete = self.provider.block_store.volumes.list()
        print(str(len(volume_list_after_delete)))

        self.assertTrue(len(volume_list_after_delete), len(volume_list_before_delete) - 1)
