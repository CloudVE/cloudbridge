import json
import unittest
import uuid

from cloudbridge.cloud.interfaces import TestMockHelperMixin

from test.helpers import ProviderTestBase
import test.helpers as helpers


class AzureObjectStoreServiceTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureObjectStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_create(self):
        container_name = "container3"
        container = self.provider.object_store.create(container_name)
        print(container)
        self.assertTrue(
            container.name == container_name,
            "Name of the container should be {0}".format(container_name))

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_list(self):
        containerList = self.provider.object_store.list()
        print("List Container - " + str(containerList))
        self.assertEqual(
            len(containerList), 1)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_find_Exist(self):
        container = self.provider.object_store.find("container1")
        print("Find Exist - " + str(container))
        self.assertEqual(
            len(container) ,1)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_find_NotExist(self):
        ## For testing the case when container does not exist
        container = self.provider.object_store.find("container3")
        print("Find Not Exist - " + str(container))
        self.assertEqual(
            len(container), 0)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_get_Exist(self):
        container = self.provider.object_store.get("container2")
        print("Get Exist - " + str(container))
        self.assertTrue(
            str(container) == "<CB-AzureBucket: container2>",
            "Object find returned value should be container3")

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_get_NotExist(self):
        container = self.provider.object_store.get("container3")
        print("Get Not Exist - " + str(container))
        self.assertEqual(
            str(container) , 'None')
