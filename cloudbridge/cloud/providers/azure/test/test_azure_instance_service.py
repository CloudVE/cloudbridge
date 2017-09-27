import cloudbridge.cloud.providers.azure.test.helpers as helpers
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_list(self):
        instances_list = self.provider.compute.instances.list()
        print("List Instances - " + str(instances_list))
        self.assertTrue(instances_list.total_results > 0)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_get_exist(self):
        instance_get = self.provider.compute.instances.get('VM1')
        print("Get Instance - " + str(instance_get))
        self.assertIsNotNone(instance_get)

    @helpers.skipIfNoService(['security.security_groups'])
    def test_azure_instances_get_Not_exist(self):
        instance_get = self.provider.compute.instances.get('VM_dontfindme')
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
        image_id = 'image3'

        img = self.provider.compute.images.get(image_id)

        self.assertIsNotNone(img)

        # TODO: Add logic to get key pair
        key_pair = self.provider.security.key_pairs.get('KeyPair1')
        self.assertIsNotNone(key_pair)

        inst_type = [t for t in self.provider.compute.instance_types.list()
                     if t.name == 'Standard_DS1_v2'][0]
        sg_id = 'sg2'
        sg = self.provider.security. \
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
