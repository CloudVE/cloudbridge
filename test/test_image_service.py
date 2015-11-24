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
        test_instance = helpers.get_test_instance(self.provider, instance_name)
        with helpers.cleanup_action(lambda: test_instance.terminate()):
            name = "CBUnitTestListImg-{0}".format(uuid.uuid4())
            test_image = test_instance.create_image(name)

            def cleanup_img(img):
                img.delete()
                img.wait_for(
                    [MachineImageState.UNKNOWN, MachineImageState.ERROR],
                    interval=self.get_test_wait_interval())

            with helpers.cleanup_action(lambda: cleanup_img(test_image)):
                test_image.wait_till_ready(
                    interval=self.get_test_wait_interval())

                self.assertTrue(
                    test_instance.id in repr(test_instance),
                    "repr(obj) should contain the object id so that the object"
                    " can be reconstructed, but does not.")

                self.assertTrue(
                    test_image.description is None or isinstance(
                        test_image.description, six.string_types),
                    "Image description must be None or a string")

                images = self.provider.compute.images.list()
                list_images = [image for image in images
                               if image.name == name]
                self.assertTrue(
                    len(list_images) == 1,
                    "List images does not return the expected image %s" %
                    name)

                # check iteration
                iter_images = [image for image in self.provider.compute.images
                               if image.name == name]
                self.assertTrue(
                    len(iter_images) == 1,
                    "Iter images does not return the expected image %s" %
                    name)

                # find image
                found_images = self.provider.compute.images.find(name=name)
                self.assertTrue(
                    len(found_images) == 1,
                    "Iter images does not return the expected image %s" %
                    name)

                get_img = self.provider.compute.images.get(
                    test_image.id)
                self.assertTrue(
                    found_images[0] == iter_images[0] == get_img == test_image,
                    "Objects returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(found_images[0].id,
                                             get_img.id,
                                             test_image.id))
                self.assertTrue(
                    list_images[0].name == found_images[0].name ==
                    get_img.name == test_image.name,
                    "Names returned by list: {0}, find: {1} and get: {2} are"
                    " not as expected: {3}" .format(list_images[0].name,
                                                    found_images[0].name,
                                                    get_img.name,
                                                    test_image.name))
            # TODO: Images take a long time to deregister on EC2. Needs
            # investigation
            images = self.provider.compute.images.list()
            found_images = [image for image in images
                            if image.name == name]
            self.assertTrue(
                len(found_images) == 0,
                "Image %s should have been deleted but still exists." %
                name)
