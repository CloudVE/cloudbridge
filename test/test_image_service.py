from cloudbridge.cloud.interfaces import MachineImageState
from cloudbridge.cloud.interfaces.resources import Instance, MachineImage

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit


class CloudImageServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['compute.images', 'networking.networks',
                              'compute.instances'])
    def test_create_and_list_image(self):
        """
        Create a new image and check whether that image can be listed.
        This covers waiting till the image is ready, checking that the image
        label is the expected one and whether list_images is functional.
        """
        instance_label = "cb-crudimage-{0}".format(helpers.get_uuid())
        img_inst_label = "cb-crudimage-{0}".format(helpers.get_uuid())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        subnet = None

        def create_img(label):
            return test_instance.create_image(label=label)

        def cleanup_img(img):
            if img:
                img.delete()
                img.wait_for(
                    [MachineImageState.UNKNOWN, MachineImageState.ERROR])
                img.refresh()
                self.assertTrue(
                    img.state == MachineImageState.UNKNOWN,
                    "MachineImage.state must be unknown when refreshing after "
                    "a delete but got %s"
                    % img.state)

        def extra_tests(img):
            # check image size
            img.refresh()
            self.assertGreater(img.min_disk, 0, "Minimum disk"
                               " size required by image is invalid")
            create_instance_from_image(img)

        def create_instance_from_image(img):
            img_instance = None
            with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                    img_instance)):
                img_instance = self.provider.compute.instances.create(
                    img_inst_label, img,
                    helpers.get_provider_test_data(self.provider, 'vm_type'),
                    subnet=subnet,
                    zone=helpers.get_provider_test_data(
                        self.provider, 'placement'))
                img_instance.wait_till_ready()
                self.assertIsInstance(img_instance, Instance)
                self.assertEqual(
                    img_instance.label, img_inst_label,
                    "Instance label {0} is not equal to the expected label"
                    " {1}".format(img_instance.label, img_inst_label))
                image_id = img.id
                self.assertEqual(img_instance.image_id, image_id,
                                 "Image id {0} is not equal to the expected id"
                                 " {1}".format(img_instance.image_id,
                                               image_id))
                self.assertIsInstance(img_instance.public_ips, list)
                if img_instance.public_ips:
                    self.assertTrue(
                        img_instance.public_ips[0],
                        "public ip should contain a"
                        " valid value if a list of public_ips exist")
                self.assertIsInstance(img_instance.private_ips, list)
                self.assertTrue(img_instance.private_ips[0],
                                "private ip should"
                                " contain a valid value")

        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance)):
            subnet = helpers.get_or_create_default_subnet(
                self.provider)
            test_instance = helpers.get_test_instance(
                self.provider, instance_label, subnet=subnet)
            sit.check_crud(self, self.provider.compute.images, MachineImage,
                           "cb-listimg", create_img, cleanup_img,
                           extra_test_func=extra_tests)
