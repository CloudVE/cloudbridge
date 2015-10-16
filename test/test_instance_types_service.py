import six
from test.helpers import ProviderTestBase


class ProviderInstanceTypesServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderInstanceTypesServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_instance_types(self):
        instance_types = self.provider.compute.instance_types.list()
        for inst_type in instance_types:
            self.assertIsNotNone(
                inst_type.id,
                "InstanceType id must have a value")
            self.assertIsNotNone(
                inst_type.name,
                "InstanceType name must have a value")
            self.assertTrue(
                inst_type.family is None or isinstance(
                    inst_type.family,
                    six.string_types),
                "InstanceType family family be None or a"
                " string but is: {0}".format(inst_type.family))
            self.assertTrue(
                inst_type.vcpus is None or (
                    isinstance(inst_type.vcpus, six.integer_types) and
                    inst_type.vcpus >= 0),
                "InstanceType vcpus family be None or a positive integer")
            self.assertTrue(
                inst_type.ram is None or inst_type.ram >= 0,
                "InstanceType ram must be None or a positive number")
            self.assertTrue(
                inst_type.root_disk is None or inst_type.root_disk >= 0,
                "InstanceType root_disk must be None or a positive number but"
                " is: {0}".format(inst_type.root_disk))
            self.assertTrue(
                inst_type.ephemeral_disk is None or
                inst_type.ephemeral_disk >= 0,
                "InstanceType ephemeral_disk must be None or a positive"
                " number")
            self.assertTrue(
                inst_type.total_disk is None or inst_type.total_disk >= 0,
                "InstanceType total_disk must be None or a positive number")
            self.assertTrue(
                inst_type.extra_data is None or isinstance(
                    inst_type.extra_data, dict),
                "InstanceType extra_data must be None or a dict")
