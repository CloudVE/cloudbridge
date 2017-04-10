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
        container = self.provider.object_store.create("container3")
        print(container)
        self.assertTrue(
            container == None,
            "Object create returned value should be None")

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_find(self):
        container = self.provider.object_store.find("container1")
        print(str(container))
        self.assertTrue(
            str(container) == "[<CB-AzureBucket: container1>]",
            "Object find returned value should be container1")

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_get(self):
        pass
