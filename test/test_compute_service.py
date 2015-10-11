import socket
import uuid

from cloudbridge.providers.interfaces import InstanceState
from test.helpers import ProviderTestBase
import test.helpers as helpers


class ProviderComputeServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderComputeServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_crud_instance(self):
        name = "CBInstCrud-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        inst = helpers.create_test_instance(self.provider, name)
        with helpers.exception_action(lambda: inst.terminate()):
            inst.wait_till_ready()
            all_instances = self.provider.compute.list_instances()
            found_instances = [i for i in all_instances if i.name == name]
            self.assertTrue(
                len(found_instances) == 1,
                "List instances does not return the expected instance %s" %
                name)
            inst.terminate()
            inst.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR])
            all_instances = self.provider.compute.list_instances()
            found_instances = [i for i in all_instances if i.name == name]
            self.assertTrue(
                len(found_instances) == 0,
                "List instances does not return the expected instance %s" %
                name)

    def _is_valid_ip(self, address):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except socket.error:  # not a valid address
            try:
                socket.inet_pton(socket.AF_INET, address)
            except socket.error:  # still not a valid address
                return False
        return True

    def test_instance_properties(self):
        instance_name = "CBInstProps-{0}-{1}".format(
            self.provider.name,
            uuid.uuid4())
        test_instance = helpers.get_test_instance(self.provider,
                                                  instance_name)
        with helpers.exception_action(lambda: test_instance.terminate()):
            self.assertEqual(
                test_instance.name, instance_name,
                "Instance name {0} is not equal to the expected name"
                " {1}".format(test_instance.name, instance_name))
            image_id = helpers.get_provider_test_data(self.provider, "image")
            self.assertEqual(test_instance.image_id, image_id,
                             "Image id {0} is not equal to the expected id"
                             " {1}".format(test_instance.image_id, image_id))
            self.assertIsInstance(test_instance.public_ips, list)
            self.assertIsInstance(test_instance.private_ips, list)
            self.assertTrue(
                self._is_valid_ip(self.test_instance.private_ips[0]))
