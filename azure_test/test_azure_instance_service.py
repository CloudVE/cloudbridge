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

    @helpers.skipIfNoService(['block_store.snapshots'])
    def test_azure_instance_create_and_get(self):
        image_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96/' \
                   'resourceGroups/CLOUDBRIDGE-AZURE/providers/' \
                   'Microsoft.Compute/images/image3'

        img = self.provider.compute.images.get(image_id)

        self.assertIsNotNone(img)

        # TODO: Add logic to get key pair
        key_pair = None
        # self.assertIsNotNone(key_pair)

        inst_type = [t for t in self.provider.compute.instance_types.list()
                     if t.name == 'Standard_DS1_v2'][0]
        sg_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                '/resourceGroups/CloudBridge-Azure' \
                '/providers/Microsoft.Network/networkSecurityGroups/sg2'
        sg = self.provider.security.\
            security_groups.get(sg_id)

        subnet = self.provider.network.subnets.list()[0]

        lc = self.provider.compute.instances.create_launch_config()

        lc.add_volume_device(
            is_root=True,
            source=img,
            size=img.min_disk if img and img.min_disk else 2,
            delete_on_terminate=True)

        inst = self.provider.compute.instances.create(
            name='test', image=img, instance_type=inst_type,
            subnet=subnet, zone=None,
            key_pair=key_pair, security_groups=[sg], user_data=None,
            launch_config=lc)

        self.assertIsNotNone(inst)

        inst.reboot()

        inst.name = 'newvmname'

        self.assertEqual(inst.name, 'newvmname')

        inst.add_security_group(sg)
        inst.refresh()

        # Check removing a security group from a running instance
        inst.remove_security_group(sg)
        inst.refresh()

        img = inst.create_image('test_image')

        self.assertIsNotNone(img)

        inst.terminate()
