import test.helpers as helpers
from test.helpers import ProviderTestBase


class AzureObjectStoreServiceTestCase(ProviderTestBase):
    def __init__(self, methodName, provider):
        super(AzureObjectStoreServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_create(self):
        container = self.provider.object_store.create("container3")
        print("Create - " + str(container))
        self.assertEqual(
            str(container), "<CB-AzureBucket: container3>")

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_list(self):
        containerList = self.provider.object_store.list()
        print("List Container - " + str(containerList))
        self.assertEqual(
            len(containerList), 2)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_find_Exist(self):
        container = self.provider.object_store.find("container")
        print("Find Exist - " + str(container))
        self.assertEqual(
            len(container), 2)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_find_NotExist(self):
        # For testing the case when container does not exist
        container = self.provider.object_store.find("container23")
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
        container = self.provider.object_store.get("container23")
        print("Get Not Exist - " + str(container))
        self.assertEqual(
            str(container), 'None')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_delete(self):
        containers = self.provider.object_store.find("container1")
        cont = containers[0]
        contDel = cont.delete()
        print("Bucket delete - " + str(contDel))
        self.assertEqual(
            contDel, True)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_create_object(self):
        containers = self.provider.object_store.find("container1")
        cont = containers[0]
        contDel = cont.create_object("block1")
        print("Create object  - " + str(contDel))
        self.assertEqual(
            str(contDel), '<CB-AzureBucketObject: block1>')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_exists__internalE(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        contDel = cont.exists("block2")
        print("List object  - " + str(contDel))
        self.assertEqual(
            str(contDel), 'True')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_exists__internalNE(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        contDel = cont.exists("blob3")
        print("List object  - " + str(contDel))
        self.assertEqual(
            str(contDel), 'False')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_list(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        contDel = cont.list()
        print("List object  - " + str(contDel))
        self.assertEqual(
            len(contDel), 2)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_get(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        contDel = cont.get("block2")
        print("List object  - " + str(contDel))
        self.assertEqual(
            str(contDel), "<CB-AzureBucketObject: block2>")

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_iter_content(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        blocks = cont.list()
        block = blocks[0]
        content = block.iter_content()
        print("Iter content  - " + str(content))
        self.assertEqual(
            content.getvalue(), b'blob2Content')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_iter_content_ifBlobNotExists(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        block = cont.get('block3')
        content = block.iter_content()
        self.assertEqual(
            content, None, 'content should be None')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_upload(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        blocks = cont.list()
        block = blocks[0]
        block.upload('blob1Content')
        self.assertEqual(
            block.iter_content().getvalue(), b'blob1Content')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_delete(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        blocks = cont.list()
        block = blocks[0]
        block.delete()
        self.assertEqual(
            len(cont.list()), 2)

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_upload_from_file(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        blocks = cont.list()
        block = blocks[0]
        block.upload_from_file('blob2Content')
        self.assertEqual(
            block.iter_content().getvalue(), b'blob2Content')

    @helpers.skipIfNoService(['object_store'])
    def test_azure_bucket_object_generate_url(self):
        containers = self.provider.object_store.find("container2")
        cont = containers[0]
        blocks = cont.list()
        block = blocks[0]
        url = block.generate_url()
        print(str(url))
        self.assertEqual(
            str(url), 'https://cloudbridgeazure.blob.core.windows.net/vhds/block1')

