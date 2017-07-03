from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureSubnetServiceTestCase(ProviderTestBase):
    def test_azure_subnet_service_list(self):
        subnets = self.provider.network.subnets.list()
        self.assertIsNotNone(subnets)
        for subnet in subnets:
            print(subnet.name)
            print(subnet.id)
            print(subnet.cidr_block)
            print("network_id" + subnet.network_id)

    def test_azure_subnet_service_list_filter_network_id(self):
        network_id = 'CloudBridgeNet4'
        subnets = self.provider.network.subnets.list(network_id)
        self.assertIsNotNone(subnets)
        for subnet in subnets:
            print(subnet.name)
            print(subnet.id)
            print(subnet.cidr_block)
            print("network_id" + subnet.network_id)

    def test_azure_subnet_service_list_filter_network_object(self):
        network_id = 'CloudBridgeNet4'
        network = self.provider.network.get(network_id)
        subnets = self.provider.network.subnets.list(network)
        self.assertIsNotNone(subnets)
        for subnet in subnets:
            print(subnet.name)
            print(subnet.id)
            print(subnet.cidr_block)
            print("network_id" + subnet.network_id)

    def test_azure_subnet_service_get(self):
        subnet_id = 'CloudBridgeNet4|$|MySN1'
        subnet = self.provider.network.subnets.get(subnet_id)
        self.assertIsNotNone(subnet)
        if subnet:
            print("Subnet found")
            print(subnet.id)
            print(subnet.name)
            print(subnet.cidr_block)
            print("network_id" + subnet.network_id)

    def test_azure_subnet_service_get_invalid_subnet(self):
        subnet_id = 'CloudBridgeNet4|$|MySN'
        subnet = self.provider.network.subnets.get(subnet_id)
        self.assertIsNone(subnet)

    def test_azure_create_and_delete_from_resource_subnet(self):
        network_id = 'CloudBridgeNet4'
        subnet = self.provider.network.\
            subnets.create(network=network_id,
                           cidr_block='10.0.0.0/24')
        self.assertIsNotNone(subnet.zone)
        self.assertIsNotNone(subnet)
        deleted = subnet.delete()
        self.assertTrue(deleted)
        deleted = subnet.delete()
        self.assertFalse(deleted)

    def test_azure_create_and_delete_from_service_subnet(self):
        network_id = 'CloudBridgeNet4'
        subnet = self.provider.network.\
            subnets.create(network=network_id,
                           name='test', cidr_block='10.0.0.0/24')
        self.assertIsNotNone(subnet)
        deleted = self.provider.network.subnets.delete(subnet)
        self.assertTrue(deleted)
        deleted = self.provider.network.subnets.delete(subnet)
        self.assertFalse(deleted)

    def test_azure_create_or_get_default_subnet(self):
        subnet = self.provider.network.\
            subnets.get_or_create_default()
        self.assertIsNotNone(subnet)
        subnet = self.provider.network. \
            subnets.get_or_create_default()
        self.assertIsNotNone(subnet)
        subnet.delete()
        self.provider.network.delete(subnet.network_id)
