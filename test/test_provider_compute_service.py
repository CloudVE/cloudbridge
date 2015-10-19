import uuid
import ipaddress
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
            inst.wait_till_ready(interval=self.get_test_wait_interval())
            all_instances = self.provider.compute.instances.list()
            found_instances = [i for i in all_instances if i.name == name]
            self.assertTrue(
                len(found_instances) == 1,
                "List instances does not return the expected instance %s" %
                name)

            get_inst = self.provider.compute.instances.get(
                inst.instance_id)
            self.assertTrue(
                found_instances[0].instance_id ==
                get_inst.instance_id == inst.instance_id,
                "Ids returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(found_instances[0].instance_id,
                                         get_inst.instance_id,
                                         inst.instance_id))
            self.assertTrue(
                found_instances[0].name ==
                get_inst.name == inst.name,
                "Names returned by list: {0} and get: {1} are not as "
                " expected: {2}" .format(found_instances[0].name,
                                         get_inst.name,
                                         inst.name))

            inst.terminate()
            inst.wait_for(
                [InstanceState.TERMINATED, InstanceState.UNKNOWN],
                terminal_states=[InstanceState.ERROR],
                interval=self.get_test_wait_interval())
            deleted_inst = self.provider.compute.instances.get(
                inst.instance_id)
            self.assertTrue(
                deleted_inst is None or deleted_inst.state in (
                    InstanceState.TERMINATED,
                    InstanceState.UNKNOWN),
                "Instance %s should have been deleted but still exists." %
                name)

    def _is_valid_ip(self, address):
        try:
            ipaddress.ip_address(address)
        except ValueError:
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
            # Must have either a public or a private ip
            ip_private = test_instance.private_ips[0] \
                if test_instance.private_ips else None
            ip_address = test_instance.public_ips[0] \
                if test_instance.public_ips else ip_private
            self.assertIsNotNone(
                ip_address,
                "Instance must have either a public IP or a private IP")
            self.assertTrue(
                self._is_valid_ip(ip_address),
                "Instance must have a valid IP address")
            test_instance.terminate()
