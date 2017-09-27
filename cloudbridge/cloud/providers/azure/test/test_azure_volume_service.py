import cloudbridge.cloud.providers.azure.test.helpers as helpers
from cloudbridge.cloud.interfaces import VolumeState
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureVolumeServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_create_and_get(self):
        volume = self.provider.block_store.volumes.create(
            "MyVolume", 1, description='My volume')
        print("Create Volume - " + str(volume))
        self.assertTrue(
            volume.name == "MyVolume", "Volume name should be MyVolume")

        self.assertIsNotNone(volume.description)
        self.assertIsNotNone(volume.name)
        self.assertIsNotNone(volume.size)
        self.assertIsNotNone(volume.zone_id)
        self.assertIsNone(volume.source)
        self.assertIsNone(volume.attachments)
        self.assertIsNotNone(volume.create_time)
        volume.name = 'newname'

        volume = self.provider.block_store.volumes.get(
            volume.id)
        volume.description = 'My Volume desc'
        print("Get Volume  - " + str(volume))
        self.assertTrue(
            volume.description == "My Volume desc",
            "Volume description should be My Volume desc")

        volume.delete()

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_delete(self):
        volume = self.provider.block_store.volumes.create("MyTestVolume", 1)
        volume.refresh()
        print("Create Volume - " + str(volume))
        self.assertTrue(volume.name == "MyTestVolume",
                        "Volume name should be MyVolume")
        volume.delete()
        volume1_id = "MyVolume"
        delete_volume = volume.delete()
        self.assertEqual(delete_volume, False)

        volume.refresh()
        self.assertEqual(volume.state, VolumeState.UNKNOWN)

        volume1 = self.provider.block_store.volumes.get(volume1_id)
        self.assertTrue(
            volume1 is None, "Volume still exists")

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_attach_and_detach(self):
        volume = self.provider.block_store.volumes.create(
            "attach", 1, description='My volume')
        self.assertTrue(
            volume.name == "attach", "Volume name should be MyVolume")
        instance_id = 'VM1'
        attached = volume.attach(instance_id)

        self.assertEqual(attached, True)
        self.assertIsNotNone(volume.attachments)
        instance_id = instance_id + '1'
        attach_volume = volume.attach(instance_id)
        self.assertEqual(attach_volume, False)

        detached = volume.detach()
        self.assertEqual(detached, True)

        detached = volume.detach()
        self.assertEqual(detached, False)

        volume.delete()

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_create_snapshot(self):
        volume = self.provider.block_store.volumes.create(
            "MyVolume", 1, description='My volume')
        self.assertTrue(
            volume.name == "MyVolume", "Volume name should be MyVolume")
        snapshot = volume.create_snapshot("MySnap")
        self.assertTrue(
            snapshot is not None, "Snapshot not created")

        volume.delete()

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_get_ifNotExist(self):
        volume_id = "MyVolume123"
        volume = self.provider.block_store.volumes.get(volume_id)
        self.assertTrue(
            volume is None, "Volume should not be available")

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_find(self):
        volumes = self.provider.block_store.volumes.find("Volume1")
        print(len(volumes))
        print('after find')
        self.assertTrue(
            len(volumes) == 1, "Volume should not be available")
        self.assertIsNotNone(volumes[0].source)

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_find_ifNotExist(self):
        volumes = self.provider.block_store.volumes.find("Volume123")
        self.assertTrue(
            len(volumes) == 0, "Volume should not be available")

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_list(self):
        volume_list = self.provider.block_store.volumes.list()
        print("Volume List - " + str(volume_list))
        self.assertEqual(
            len(volume_list), 2)
