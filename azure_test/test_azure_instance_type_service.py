import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


class AzureInstanceTypeServiceTestCase(ProviderTestBase):

    @helpers.skipIfNoService(['compute.instance_types'])
    def test_azure_instance_type_list(self):
        instance_type_list = self.provider.compute.instance_types.list()
        print("List Instance Types - " + str(instance_type_list))
        print("List Instance Type Properties - ")
        print("Name - " + str(instance_type_list[0].name))
        print("vcpus - " + str(instance_type_list[0].vcpus))
        print("ram - " + str(instance_type_list[0].ram))
        print("size_ephemeral_disks - " +
              str(instance_type_list[0].size_ephemeral_disks))
        print("num_ephemeral_disks - " +
              str(instance_type_list[0].num_ephemeral_disks))
        self.assertTrue(instance_type_list.total_results > 0)
