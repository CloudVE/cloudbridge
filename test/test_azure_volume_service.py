import json
import unittest
import uuid

from cloudbridge.cloud.interfaces import TestMockHelperMixin

from test.helpers import ProviderTestBase
import test.helpers as helpers


class AzureVolumeServiceTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureVolumeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)
        self.snapshots = self.provider.block_store.snapshots

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_create(self):
        volume = self.provider.block_store.volumes.create("MyVolume",1, description='My volume')
        print("Create Volume - " + str(volume))
        self.assertTrue(
            volume.name == "MyVolume" , "Volume name should be MyVolume")


    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_get(self):
        volume = self.provider.block_store.volumes.get("MyVolume")
        print("Get Volume  - " + str(volume))
        self.assertTrue(
            volume.name == "MyVolume", "Volume name should be MyVolume")

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_find(self):
        with self.assertRaises(NotImplementedError):
            volumes = self.provider.block_store.volumes.find("MyVolume")

    @helpers.skipIfNoService(['block_store.volumes'])
    def test_azure_volume_list(self):
        volume_list = self.provider.block_store.volumes.list()
        print("Volume List - " + str(volume_list))
        self.assertEqual(
            len(volume_list), 3)
