import uuid

from cloudbridge.cloud.providers.azure.integration_test import helpers
from cloudbridge.cloud.providers.azure. \
    integration_test.helpers import ProviderTestBase


class AzureIntegrationInstanceServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['compute.instances'])
    def test_azure_instance_service(self):
        instance_name = 'CbAzure-{0}'.format(uuid.uuid4().hex[:6])
        image_name = 'CbAzure-img-{0}'.format(uuid.uuid4().hex[:6])
        security_group_name = 'CbAzure-sg-{0}'.format(uuid.uuid4().hex[:6])
        network_name = 'CbAzure-net-{0}'.format(uuid.uuid4().hex[:6])
        subnet_name = 'CbAzure-subnet-{0}'.format(uuid.uuid4().hex[:6])
        key_pair_name = 'CbAzure-keypair-{0}'.format(uuid.uuid4().hex[:6])

        image_id = 'CbTest-Img'

        img = self.provider.compute.images.get(image_id)

        self.assertIsNotNone(img)

        key_pair = self.provider.security. \
            key_pairs.create(key_pair_name)

        self.assertIsNotNone(key_pair)

        with open('{0}.pem'.format(key_pair_name), 'w') as f:
            f.write(key_pair.material)

        inst_type = [t for t in self.provider.compute.instance_types.list()
                     if t.name == 'Standard_DS2_v2'][0]

        net = self.provider.network.create(network_name)

        self.assertIsNotNone(net)

        subnet = net.create_subnet('10.0.0.0/23', name=subnet_name)

        self.assertIsNotNone(subnet)

        sg = self.provider.security.security_groups. \
            create(security_group_name,
                   'A security group used by CloudBridge', '')

        self.assertIsNotNone(sg)

        sg.add_rule('tcp', 22, 22, '0.0.0.0/0')

        new_security_group_name = 'CbAzure-sg-{0}'.format(uuid.uuid4().hex[:6])

        new_sg = self.provider.security.security_groups. \
            create(new_security_group_name,
                   'A security group used by CloudBridge', '')

        self.assertIsNotNone(new_sg)

        new_sg.add_rule('*', 0, 65535, '*')

        lc = self.provider.compute.instances.create_launch_config()

        volume = self.provider.block_store. \
            volumes.create('CbAzure-Vol-{0}'.format(uuid.uuid4().hex[:6]), 30)

        volume.wait_till_ready()

        self.assertIsNotNone(volume)

        snapshot = volume. \
            create_snapshot('CbAzure-Snap-{0}'.format(uuid.uuid4().hex[:6]))

        snapshot.wait_till_ready()

        self.assertIsNotNone(snapshot)

        lc.add_volume_device(
            is_root=False,
            source=volume,
            size=volume.size,
            delete_on_terminate=True)

        lc.add_volume_device(
            is_root=False,
            source=snapshot,
            size=snapshot.size,
            delete_on_terminate=True)

        lc.add_volume_device(
            is_root=False,
            source=None,
            size=40,
            delete_on_terminate=True)

        inst = self.provider.compute.instances.create(
            name=instance_name, image=img, instance_type=inst_type,
            subnet=subnet, zone=None,
            key_pair=key_pair, security_groups=[sg, new_sg],
            user_data=None,
            launch_config=lc)

        inst.wait_till_ready()

        floating_ip = self.provider.network.create_floating_ip()

        self.assertIsNotNone(floating_ip)

        inst.add_floating_ip(floating_ip.public_ip)

        inst.refresh()

        self.assertIsNotNone(inst.public_ips[0])

        img = inst.create_image(image_name)

        self.assertIsNotNone(img)

        inst.terminate()

        subnet.delete()

        net.delete()

        sg.delete()

        new_sg.delete()

        img.delete()

        volume.delete()

        snapshot.delete()
