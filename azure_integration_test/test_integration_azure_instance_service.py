import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.images'])
    def test_azure_instance_service(self):
        instances_list = self.provider.compute.instances.list()
        print("List Instances - " + str(instances_list))
        print("Properties - ")
        print("Id - " + str(instances_list[0].id))
        print("name - " + str(instances_list[0].name))
        print("public_ips - " + str(instances_list[0].public_ips))
        print("private_ips - " + str(instances_list[0].private_ips))
        print("instance_type_id - " + str(instances_list[0].instance_type_id))
        print("instance_type - " + str(instances_list[0].instance_type))
        print("image_id - " + str(instances_list[0].image_id))
        print("zone_id - " + str(instances_list[0].zone_id))
        print("security_groups - " +
              str(instances_list[0].security_groups))
        print("security_group_ids - " +
              str(instances_list[0].security_group_ids))
        print("key_pair_name - " + str(instances_list[0].key_pair_name))
        print("state - " + str(instances_list[0].state))

        print("Count - " + str(len(instances_list)))
        self.assertTrue(len(instances_list) > 0)

        instance_get = self.provider.compute.instances. \
            get(instances_list[0].id)
        print("Get Instance - " + str(instance_get))
        self.assertIsNotNone(instance_get)

        instance_find = self.provider.compute.instances. \
            find(instances_list[0].name)
        print("Find Instance - " + str(instance_find))
        self.assertTrue(len(instance_find) > 0)
