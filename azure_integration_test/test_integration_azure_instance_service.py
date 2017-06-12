import uuid

import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.instances'])
    def test_azure_instance_service(self):
        instance_name = 'CbAzure-test6-{0}'.format(uuid.uuid4().hex[:6])
        # image_name = 'CbAzure-img-{0}'.format(uuid.uuid4().hex[:6])
        security_group_name = 'CbAzure-sg-{0}'.format(uuid.uuid4().hex[:6])
        network_name = 'CbAzure-net-{0}'.format(uuid.uuid4().hex[:6])
        subnet_name = 'CbAzure-subnet-{0}'.format(uuid.uuid4().hex[:6])
        # key_pair_name = 'CbAzure-keypair-4e36b7'

        image_id = 'CBAZURE-USER-TEST-IMG'

        img = self.provider.compute.images.get(image_id)

        self.assertIsNotNone(img)

        # key_pair = self.provider.security.\
        #     key_pairs.create(key_pair_name)
        #
        # self.assertIsNotNone(key_pair)
        #
        # with open('{0}.pem'.format(key_pair_name), 'w') as f:
        #     f.write(key_pair.material)

        inst_type = [t for t in self.provider.compute.instance_types.list()
                     if t.name == 'Standard_DS2_v2'][0]

        net = self.provider.network.create(network_name)

        self.assertIsNotNone(net)

        subnet = net.create_subnet('10.0.0.0/23', name=subnet_name)

        self.assertIsNotNone(subnet)

        sg = self.provider.security.security_groups.\
            create(security_group_name,
                   'A security group used by CloudBridge', '')

        self.assertIsNotNone(sg)

        sg.add_rule('tcp', 22, 22, '0.0.0.0/0')

        # lc = self.provider.compute.instances.create_launch_config()
        #
        # volume = self.provider.block_store.\
        #     volumes.create('CbAzure-Vol-{0}'.
        # format(uuid.uuid4().hex[:6]), 30)
        #
        # volume.wait_till_ready()
        #
        # self.assertIsNotNone(volume)
        #
        # snapshot = volume.\
        #     create_snapshot('CbAzure-Snap-{0}'.format(uuid.uuid4().hex[:6]))
        #
        # snapshot.wait_till_ready()
        #
        # self.assertIsNotNone(snapshot)
        #
        # lc.add_volume_device(
        #     is_root=False,
        #     source=volume,
        #     size=volume.size,
        #     delete_on_terminate=True)
        #
        # lc.add_volume_device(
        #     is_root=False,
        #     source=snapshot,
        #     size=snapshot.size,
        #     delete_on_terminate=True)
        #
        # lc.add_volume_device(
        #     is_root=False,
        #     source=None,
        #     size=40,
        #     delete_on_terminate=True)

        inst = self.provider.compute.instances.create(
            name=instance_name, image=img, instance_type=inst_type,
            subnet=subnet, zone=None,
            key_pair=None, security_groups=None, user_data=None,
            launch_config=None)

        inst.wait_till_ready()

        floating_ip = self.provider.network.create_floating_ip()

        self.assertIsNotNone(floating_ip)

        inst.add_floating_ip(floating_ip.public_ip)

        inst.refresh()

        self.assertIsNotNone(inst.public_ips[0])

        # inst = self.provider.compute.instances.
        # get('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96
        # /resourceGroups/CB-INST-DEMO-RG/providers/
        # Microsoft.Compute/virtualMachines/CbAzure-inst-304a17-968334')
        #
        # img = inst.\
        #     create_image(image_name)
        # self.assertIsNotNone(img)

        # inst.terminate()
        #
        # subnet.delete()
        #
        # net.delete()
        #
        # sg.delete()
        #
        # snapshot.delete()
        #
        # img.delete()
