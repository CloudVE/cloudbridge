import uuid

from test import helpers
from test.helpers import ProviderTestBase

from cloudbridge.cloud.interfaces import MachineImageState
from cloudbridge.cloud.interfaces import TestMockHelperMixin

import six


class CloudImageServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['compute.images', 'network',
                              'compute.instances'])
    def test_create_and_list_image(self):
        """
        Create a new image and check whether that image can be listed.
        This covers waiting till the image is ready, checking that the image
        name is the expected one and whether list_images is functional.
        """
        instance_name = "CBImageTest-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())

        # Declare these variables and late binding will allow
        # the cleanup method access to the most current values
        test_instance = None
        net = None
        with helpers.cleanup_action(lambda: helpers.cleanup_test_resources(
                test_instance, net)):
            net, subnet = helpers.create_test_network(
                self.provider, instance_name)
            test_instance = helpers.get_test_instance(
                self.provider, instance_name, subnet=subnet)

            name = "CBUnitTestListImg-{0}".format(uuid.uuid4())
            test_image = test_instance.create_image(name)

            def cleanup_img(img):
                img.delete()
                img.wait_for(
                    [MachineImageState.UNKNOWN, MachineImageState.ERROR])

            with helpers.cleanup_action(lambda: cleanup_img(test_image)):
                test_image.wait_till_ready()

                self.assertTrue(
                    test_instance.id in repr(test_instance),
                    "repr(obj) should contain the object id so that the object"
                    " can be reconstructed, but does not.")

                self.assertTrue(
                    test_image.description is None or isinstance(
                        test_image.description, six.string_types),
                    "Image description must be None or a string")

                # This check won't work when >50 images are available
                # images = self.provider.compute.images.list()
                # list_images = [image for image in images
                #                if image.name == name]
                # self.assertTrue(
                #     len(list_images) == 1,
                #     "List images does not return the expected image %s" %
                #     name)

                # check iteration
                iter_images = [image for image in self.provider.compute.images
                               if image.name == name]
                self.assertTrue(
                    name in [ii.name for ii in iter_images],
                    "Iter images (%s) does not contain the expected image %s" %
                    (iter_images, name))

                # find image
                found_images = self.provider.compute.images.find(name=name)
                self.assertTrue(
                    name in [fi.name for fi in found_images],
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
                self.assertTrue(
                    found_images[0].name == get_img.name == test_image.name,
                    "Names returned by find: {0} and get: {1} are"
                    " not as expected: {2}" .format(found_images[0].name,
                                                    get_img.name,
                                                    test_image.name))
                # TODO: Fix moto so that the BDM is populated correctly
                if not isinstance(self.provider, TestMockHelperMixin):
                    # check image size
                    self.assertGreater(get_img.min_disk, 0, "Minimum disk size"
                                       " required by image is invalid")
            # TODO: Images take a long time to deregister on EC2. Needs
            # investigation
            images = self.provider.compute.images.list()
            found_images = [image for image in images
                            if image.name == name]
            self.assertTrue(
                len(found_images) == 0,
                "Image %s should have been deleted but still exists." %
                name)
