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

        # volumes_count1 = len(self.provider.block_store.volumes.list())

        volume = self.provider.block_store.volumes.create(volume_name, 1)
        volume_id= volume.id
        self.assertTrue(volume is not None , 'Volume {0} not created'.format(volume_name))

        # volumes_count2 = len(self.provider.block_store.volumes.list())
        # self.assertTrue(volumes_count2 > volumes_count1, 'Volume {0} not present in list'.format(volume_name))

        # find_volume = self.provider.block_store.volumes.find(volume_name)
        # self.assertTrue(len(find_volume) == 1, 'Volume {0} not found'.format(volume_name))

        # get_volume = self.provider.block_store.volumes.get(volume.id)
        # self.assertTrue(get_volume is not None, 'Unable to get the volume {0}'.format(volume_name))

        volume.attach('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/resourceGroups/CloudBridge-Azure/providers/Microsoft.Compute/virtualMachines/ubuntu-intro2')
        #TODO: Add logic to verify that disk is attached to instance

        volume.detach()
        #TODO: Add logic to verify that disk is not in use

        # snapshot = volume.create_snapshot(snapshot_name)
        # self.assertTrue(snapshot is not None, 'Snapshot {0} not created'.format(snapshot_name))

        volume.refresh()
        self.assertTrue(volume.id == volume_id, 'Volume id should match on refresh')

        volume.delete()
        # deleted_volume = self.provider.block_store.volumes.get(volume.id)
        # self.assertTrue(deleted_volume is None, 'Volume {0} not deleted'.format(volume_name))
