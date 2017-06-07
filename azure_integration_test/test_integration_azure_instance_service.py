import uuid

import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.instances'])
    def test_azure_instance_service(self):
        instance_name = 'CbAzure-inst-{0}'.format(uuid.uuid4().hex[:6])
        image_name = 'CbAzure-img-{0}'.format(uuid.uuid4().hex[:6])
        security_group_name = 'CbAzure-sg-{0}'.format(uuid.uuid4().hex[:6])
        # key_pair_name = 'CbAzure-keypair-{0}'.format(uuid.uuid4().hex[:6])

        image_id = '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96' \
                   '/resourceGroups/VM-TEST-RG/providers' \
                   '/Microsoft.Compute/images/CbAzure-da80a6'

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
                     if t.name == 'Standard_DS1_v2'][0]

        sg = self.provider.security.security_groups.\
            create(security_group_name,
                   'A security group used by CloudBridge', '')
        sg.add_rule('tcp', 22, 22, '0.0.0.0/0')

        subnet = self.provider.network.subnets.list()[1]

        inst = self.provider.compute.instances.create(
            name=instance_name, image=img, instance_type=inst_type,
            subnet=subnet, zone=None,
            key_pair=None, security_groups=None, user_data=None,
            launch_config=None)

        inst.wait_till_ready()

        # floating_ip = self.provider.network.create_floating_ip()
        #
        # self.assertIsNotNone(floating_ip)
        #
        # inst.add_floating_ip(floating_ip.public_ip)
        #
        # inst.refresh()
        #
        # self.assertIsNotNone(inst.public_ips[0])

        instance = self.provider.compute.\
            instances.find(name=instance_name)[0]

        self.assertIsNotNone(instance)

        new_img = instance.create_image(image_name)
        self.assertIsNotNone(new_img)

        instance.terminate()
