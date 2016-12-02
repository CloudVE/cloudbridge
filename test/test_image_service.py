import uuid
import six

from cloudbridge.cloud.interfaces import MachineImageState
from test.helpers import ProviderTestBase
import test.helpers as helpers


class CloudImageServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudImageServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_create_and_list_image(self):
        """
        Create a new image and check whether that image can be listed.
        This covers waiting till the image is ready, checking that the image
        name is the expected one and whether list_images is functional.
        """
        instance_name = "CBImageTest-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        net, _ = helpers.create_test_network(self.provider, instance_name)
        test_instance = helpers.get_test_instance(self.provider, instance_name,
                                                  network=net)
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            name = "CBUnitTestListImg-{0}".format(uuid.uuid4())
            test_image = test_instance.create_image(name)

            def cleanup_img(img):
                img.delete()
                img.wait_for(
                    [MachineImageState.UNKNOWN, MachineImageState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_img(test_image)):
                self.assertTrue(
                    test_instance.id in repr(test_instance),
                    "repr(obj) should contain the object id so that the object"
                    " can be reconstructed, but does not.")

                self.assertTrue(
                    test_image.description is None or isinstance(
                        test_image.description, six.string_types),
                    "Image description must be None or a string")

                # check iteration
                # iter_images = [image for image in self.provider.compute.images
                #                if image.name == name]
                # self.assertTrue(
                #     len(iter_images) == 1,
                #     "Iter images does not return the expected image %s" %
                #     name)

                # find image
                found_images = self.provider.compute.images.find(name)
                self.assertTrue(
                    len(found_images) == 1,
                    "Find images error: expected image %s but found: %s" %
                    (name, found_images))

                # check non-existent find
                ne_images = self.provider.compute.images.find(
                    name="non_existent")
                self.assertTrue(
                    len(ne_images) == 0,
                    "Find() for a non-existent image returned %s" %
                    ne_images)

                get_img = self.provider.compute.images.get(
                    test_image.id)
                self.assertTrue(
                    found_images[0] == get_img == test_image,
                    "Objects returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(found_images[0].id,
                                             get_img.id,
                                             test_image.id))
            # It's currently not possible to "delete" EC2 images, only
            # to deallocate them. Images remain in the list but attempting
            # to access properties (name, description, state) will results
            # in an AttributeError which gets passed back as "None" to us.
            # found_images = self.provider.compute.images.find(name)
            # self.assertTrue(
            #     len(found_images) == 0 or found_images[0].name is None,
            #     "Image %s should have been deleted but still exists." %
            #     name)
