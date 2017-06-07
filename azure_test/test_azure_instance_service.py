import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


class AzureInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_list(self):
        instances_list = self.provider.compute.instances.list()
        print("List Instances - " + str(instances_list))
        self.assertTrue(instances_list.total_results > 0)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_get_exist(self):
        instance_get = self.provider.compute.instances. \
            get('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/'
                'resourceGroups/cloudbridge-azure/providers/'
                'Microsoft.Compute/virtualMachines/VM1')
        print("Get Instance - " + str(instance_get))
        self.assertIsNotNone(instance_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_get_Not_exist(self):
        instance_get = self.provider.compute.instances. \
            get('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/'
                'resourceGroups/cloudbridge-azure/providers/'
                'Microsoft.Compute/virtualMachines/VM_dontfindme')
        print("Get Instance Not Exist - " + str(instance_get))
        self.assertIsNone(instance_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_find(self):
        instance_find = self.provider.compute.instances. \
            find('VM1')
        print("Find Instance - " + str(instance_find))
        self.assertIsNotNone(instance_find)
