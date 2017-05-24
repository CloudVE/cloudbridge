import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


class AzureImageServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_list(self):
        images_list = self.provider.compute.images.list()
        print("List Images - " + str(images_list))
        self.assertTrue(images_list.total_results > 0)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_get_exist(self):
        image1_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/CLOUDBRIDGE-AZURE/providers/' \
                    'Microsoft.Compute/images/image1'
        image_get = self.provider.compute.images.get(image1_id)
        print("Get Image Exist - " + str(image_get))
        print(str(image_get.min_disk))
        print(str(image_get.state))
        self.assertIsNone(image_get.description)
        image_get.name = 'newname'
        self.assertEqual(image_get.name, 'newname')
        image_get.description = 'newdesc'
        self.assertEqual(image_get.description, 'newdesc')
        image_get.refresh()
        image_get.delete()
        image_get.refresh()
        self.assertIsNotNone(image_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_images_get_notExist(self):
        image1_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                    'resourceGroups/CLOUDBRIDGE-AZURE/providers/' \
                    'Microsoft.Compute/images/imageNotExist'
        image_get = self.provider.compute.images.get(image1_id)
        print("Get Image Not Exist- " + str(image_get))
        self.assertIsNone(image_get)

    @helpers.skipIfNoService(['compute.images'])
    def test_azure_image_find_exists(self):
        images = self.provider.compute.images.find("image1")
        for image in images:
            self.assertTrue("image" in image.name)
            print("Find Image  - " + str(image))
        print(images.total_results)
        self.assertTrue(images.total_results > 0)

    @helpers.skipIfNoService(['compute.images'])
    def test_azure_image_find_not_exists(self):
        images = self.provider.compute.images.find('dontfindme')
        self.assertTrue(images.total_results == 0)
