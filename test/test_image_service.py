from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit

from cloudbridge.cloud.interfaces import MachineImageState
from cloudbridge.cloud.interfaces.resources import MachineImage


class CloudImageServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['compute.images', 'networking.networks',
                              'compute.instances'])
    def test_create_and_list_image(self):
        """
        Create a new image and check whether that image can be listed.
        This covers waiting till the image is ready, checking that the image
        name is the expected one and whether list_images is functional.
        """
        instance_name = "cb_crudimage-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        net = None

        def create_img(name):
            return test_instance.create_image(name)

        def cleanup_img(img):
            img.delete()
            img.wait_for(
                [MachineImageState.UNKNOWN, MachineImageState.ERROR])

        def extra_tests(img):
            # check image size
            img.refresh()
            self.assertGreater(img.min_disk, 0, "Minimum disk"
                               " size required by image is invalid")

        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, instance_name)
            test_instance = helpers.get_test_instance(
                self.provider, instance_name, subnet=subnet)

            sit.check_crud(self, self.provider.compute.images, MachineImage,
                           "cb_listimg", create_img, cleanup_img,
                           extra_test_func=extra_tests)
