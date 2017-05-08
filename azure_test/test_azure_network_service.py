import test.helpers as helpers
from test.helpers import ProviderTestBase


class AzureNetworkServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_list(self):
        networks = self.provider.network.list()
        for network in networks:
            print("List( " + "Name: " + network.name + ", Id: " +
                  str(network.id) + ", State: " + network.state +
                  ", Cidr_Block: " + str(network.cidr_block) + " )")
        self.assertTrue(len(networks) == 2, "Count should be 2")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_list_check_values(self):
        networks = self.provider.network.list()
        for network in networks:
            print("List( " + "Name: " + network.name + ", Id: " +
                  str(network.id) + ", State: " + network.state +
                  ", Cidr_Block: " + str(network.cidr_block) + " )")
        self.assertTrue(len(networks) == 2, "Count should be 2")
        self.assertEqual(networks[0].id,
                         '/subscriptions'
                         '/7904d702-e01c-4826-8519-f5a25c866a96'
                         '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                         '/Microsoft.Network/virtualNetworks/CloudBridgeNet1')
        self.assertEqual(networks[0].name, "CloudBridgeNet1")
        self.assertEqual(networks[0].cidr_block,
                         "{'address_prefixes': ['10.0.0.0/16']}")
        self.assertEqual(networks[0].state, "available")
        self.assertEqual(networks[1].id,
                         '/subscriptions'
                         '/7904d702-e01c-4826-8519-f5a25c866a96'
                         '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                         '/Microsoft.Network/virtualNetworks/CloudBridgeNet2')
        self.assertEqual(networks[1].name, "CloudBridgeNet2")
        self.assertEqual(networks[1].cidr_block,
                         "{'address_prefixes': ['10.0.0.0/16']}")
        self.assertEqual(networks[1].state, "unknown")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_get_exist(self):
        network = self.provider.network \
            .get('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'
                 '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                 '/Microsoft.Network/virtualNetworks/CloudBridgeNet1')
        print("get exist: " + str(network))
        self.assertEqual(network.id,
                         '/subscriptions'
                         '/7904d702-e01c-4826-8519-f5a25c866a96'
                         '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                         '/Microsoft.Network/virtualNetworks/CloudBridgeNet1')
        self.assertEqual(network.name, "CloudBridgeNet1")
        self.assertEqual(network.cidr_block,
                         "{'address_prefixes': ['10.0.0.0/16']}")
        self.assertEqual(network.state, "available")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_get_doesnt_exist(self):
        network = self.provider.network \
            .get('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'
                 '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                 '/Microsoft.Network/virtualNetworks/CloudBridgeNet10')
        print("get does not exist: " + str(network))
        self.assertEqual(
            str(network), 'None')

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_get_with_invaid_networkid_throws(self):
        with self.assertRaises(Exception) as context:
            network = self.provider.network \
                .get('invalidNetworkId')
            print("Get with invalid network id: " + str(network))
            self.assertTrue(
                'Invalid url parameter passed' in context.exception)

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_create(self):
        network = self.provider.network.create("CloudBridgeNet1")
        print("create: " + str(network))
        self.assertEqual(network.id,
                         '/subscriptions'
                         '/7904d702-e01c-4826-8519-f5a25c866a96'
                         '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                         '/Microsoft.Network/virtualNetworks/CloudBridgeNet1')
        self.assertEqual(network.name, "CloudBridgeNet1")
        self.assertEqual(network.cidr_block,
                         "{'address_prefixes': ['10.0.0.0/16']}")
        self.assertEqual(network.state, "available")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_networkid_exists(self):
        network = self.provider.network.delete(
            '/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'
            '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
            '/Microsoft.Network/virtualNetworks/CloudBridgeNet3')
        print("Delete Network Id exist: " + str(network))
        self.assertEqual(network, True)

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_networkid_doesnotexist(self):
        network = self.provider.network \
            .delete('/subscriptions/7904d702-e01c-4826-8519-f5a25c866a96'
                    '/resourceGroups/CLOUDBRIDGE-AZURE/providers'
                    '/Microsoft.Network/virtualNetworks/CloudBridgeNet10')
        print("Delete Network Id does not exist: " + str(network))
        self.assertEqual(network, False)

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_with_invaid_networkid_throws(self):
        with self.assertRaises(Exception) as context:
            network = self.provider.network \
                .delete('invalidNetworkId')
            print("Delete with invalid network id: " + str(network))
            self.assertTrue(
                'Invalid url parameter passed' in context.exception)
