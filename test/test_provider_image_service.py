import uuid
from cloudbridge.providers.interfaces import MachineImageState
from test.helpers import ProviderTestBase
import test.helpers as helpers


class ProviderImageServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderImageServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def setUp(self):
        self.instance = helpers.get_test_instance(self.provider)

    def tearDown(self):
        self.instance.terminate()

    def test_create_and_list_image(self):
        """
        Create a new image and check whether that image can be listed.
        This covers waiting till the image is ready, checking that the image
        name is the expected one and whether list_images is functional.
        """
        name = "CBUnitTestListImg-{0}".format(uuid.uuid4())
        test_image = self.instance.create_image(name)
        with helpers.exception_action(lambda x: test_image.delete()):
            test_image.wait_till_ready()
            images = self.provider.images.list_images()
            found_images = [image for image in images if image.name == name]
            self.assertTrue(
                len(found_images) == 1,
                "List images does not return the expected image %s" %
                name)
            test_image.delete()
            test_image.wait_for(
                [MachineImageState.UNKNOWN],
                terminal_states=[MachineImageState.ERROR])
            # TODO: Images take a long time to deregister on EC2. Needs
            # investigation
#             images = self.provider.images.list_images()
#             found_images = [image for image in images if image.name == name]
#             self.assertTrue(
#                 len(found_images) == 0,
#                 "Image %s should have been deleted but still exists." %
#                 name)
