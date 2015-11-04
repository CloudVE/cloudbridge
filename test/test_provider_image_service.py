import uuid
import six
from cloudbridge.cloud.interfaces import MachineImageState
from test.helpers import ProviderTestBase
import test.helpers as helpers


class ProviderImageServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderImageServiceTestCase, self).__init__(
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
                    [MachineImageState.UNKNOWN],
                    terminal_states=[MachineImageState.ERROR],
                    interval=self.get_test_wait_interval())

            with helpers.cleanup_action(lambda: cleanup_img(test_image)):
                test_image.wait_till_ready(
                    interval=self.get_test_wait_interval())

                self.assertTrue(
                    test_image.description is None or isinstance(
                        test_image.description, six.string_types),
                    "Image description must be None or a string")

                images = self.provider.images.list()
                found_images = [image for image in images
                                if image.name == name]
                self.assertTrue(
                    len(found_images) == 1,
                    "List images does not return the expected image %s" %
                    name)

                get_img = self.provider.images.get(
                    test_image.image_id)
                self.assertTrue(
                    found_images[0].image_id ==
                    get_img.image_id == test_image.image_id,
                    "Ids returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(found_images[0].image_id,
                                             get_img.image_id,
                                             test_image.image_id))
                self.assertTrue(
                    found_images[0].name ==
                    get_img.name == test_image.name,
                    "Names returned by list: {0} and get: {1} are not as "
                    " expected: {2}" .format(found_images[0].name,
                                             get_img.name,
                                             test_image.name))
            # TODO: Images take a long time to deregister on EC2. Needs
            # investigation
            images = self.provider.images.list()
            found_images = [image for image in images
                            if image.name == name]
            self.assertTrue(
                len(found_images) == 0,
                "Image %s should have been deleted but still exists." %
                name)
