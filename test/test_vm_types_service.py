import six

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit


class CloudVMTypeServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['compute.vm_types'])
    def test_vm_type_properties(self):

        for vm_type in self.provider.compute.vm_types:
            sit.check_repr(self, vm_type)
            self.assertIsNotNone(
                vm_type.id,
                "VMType id must have a value")
            self.assertIsNotNone(
                vm_type.name,
                "VMType name must have a value")
            self.assertTrue(
                vm_type.family is None or isinstance(
                    vm_type.family,
                    six.string_types),
                "VMType family must be None or a"
                " string but is: {0}".format(vm_type.family))
            self.assertTrue(
                vm_type.vcpus is None or (
                    isinstance(vm_type.vcpus, six.integer_types) and
                    vm_type.vcpus >= 0),
                "VMType vcpus must be None or a positive integer but is: {0}"
                .format(vm_type.vcpus))
            self.assertTrue(
                vm_type.ram is None or vm_type.ram >= 0,
                "VMType ram must be None or a positive number")
            self.assertTrue(
                vm_type.size_root_disk is None or
                vm_type.size_root_disk >= 0,
                "VMType size_root_disk must be None or a positive number"
                " but is: {0}".format(vm_type.size_root_disk))
            self.assertTrue(
                vm_type.size_ephemeral_disks is None or
                vm_type.size_ephemeral_disks >= 0,
                "VMType size_ephemeral_disk must be None or a positive"
                " number")
            self.assertTrue(
                isinstance(vm_type.num_ephemeral_disks,
                           six.integer_types) and
                vm_type.num_ephemeral_disks >= 0,
                "VMType num_ephemeral_disks must be None or a positive"
                " number")
            self.assertTrue(
                vm_type.size_total_disk is None or
                vm_type.size_total_disk >= 0,
                "VMType size_total_disk must be None or a positive"
                " number")
            self.assertTrue(
                vm_type.extra_data is None or isinstance(
                    vm_type.extra_data, dict),
                "VMType extra_data must be None or a dict")

    @helpers.skipIfNoService(['compute.vm_types'])
    def test_vm_types_standard(self):
        """
        Searching for an instance by name should return an
        VMType object and searching for a non-existent
        object should return an empty iterator
        """
        vm_type_name = helpers.get_provider_test_data(
            self.provider,
            "vm_type")
        vm_type = self.provider.compute.vm_types.find(
            name=vm_type_name)[0]

        sit.check_standard_behaviour(
                self, self.provider.compute.vm_types, vm_type)
