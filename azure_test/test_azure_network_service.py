import azure_test.helpers as helpers
from azure_test.helpers import ProviderTestBase


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
        self.assertEqual(networks[0].id, 'CloudBridgeNet1')
        self.assertEqual(networks[0].name, "CloudBridgeNet1")
        self.assertEqual(networks[0].cidr_block,
                         '10.0.0.0/16')
        self.assertEqual(networks[0].state, "available")
        self.assertEqual(networks[1].id, 'CloudBridgeNet2')
        self.assertEqual(networks[1].name, "CloudBridgeNet2")
        self.assertEqual(networks[1].cidr_block,
                         '10.0.0.0/16')
        self.assertEqual(networks[1].state, "unknown")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_get_exist(self):
        network = self.provider.network.get('CloudBridgeNet1')
        print("get exist: " + str(network))
        self.assertEqual(network.id, 'CloudBridgeNet1')
        self.assertEqual(network.name, "CloudBridgeNet1")
        self.assertEqual(network.cidr_block,
                         '10.0.0.0/16')
        self.assertEqual(network.state, "available")

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_get_doesnt_exist(self):
        network = self.provider.network.get('CloudBridgeNet10')
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
        network.refresh()
        print("create: " + str(network))
        self.assertIsNotNone(network.id)
        self.assertEqual(network.name, "CloudBridgeNet1")
        self.assertEqual(network.cidr_block,
                         '10.0.0.0/16')
        self.assertEqual(network.state, "available")
        self.assertTrue(network.external)
        network.name = 'newname'
        self.assertEqual(network.name, 'newname')
        deleted = network.delete()
        self.assertTrue(deleted)
        deleted = network.delete()
        self.assertFalse(deleted)
        network.refresh()

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_networkid_exists(self):
        isdeleted = self.provider.network.delete('CloudBridgeNet3')

        print("Delete Network Id exist: " + str(isdeleted))
        self.assertEqual(isdeleted, True)

        # Calling get network to make sure network was actually deleted
        network = self.provider.network.get('CloudBridgeNet3')
        print("get does not exist: " + str(network))

        self.assertEqual(
            str(network), 'None')

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_networkid_does_not_exist(self):
        isdeleted = self.provider.network.delete('CloudBridgeNet10')

        print("Delete Network Id does not exist: " + str(isdeleted))
        self.assertEqual(isdeleted, False)

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_delete_with_invaid_networkid_throws(self):
        with self.assertRaises(Exception) as context:
            isdeleted = self.provider.network \
                .delete('invalidNetworkId')
            print("Delete with invalid network id: " + str(isdeleted))
            self.assertTrue(
                'Invalid url parameter passed' in context.exception)

    def test_network_create_and_list_subnet(self):
        network = self.provider.network.get('CloudBridgeNet1')

        subnet = network.create_subnet('10.0.0.0/24')
        self.assertIsNotNone(subnet)
        subnets = network.subnets()
        self.assertTrue(len(subnets) > 0)
        subnet.delete()

    @helpers.skipIfNoService(['network'])
    def test_azure_network_service_crud_floating_ips(self):
        floating_ips = self.provider.network.floating_ips()
        self.assertTrue(len(floating_ips) == 3, "Count should be 3")

        floating_ip = self.provider.network.create_floating_ip()
        print("create: " + str(floating_ip))
        self.assertEqual(floating_ip.public_ip, '13.82.104.38')
        self.assertEqual(floating_ip.private_ip, None)

        floating_ips = self.provider.network.floating_ips()
        self.assertTrue(len(floating_ips) == 4, "Count should be 4")

        floating_ip.delete()

        floating_ips = self.provider.network.floating_ips()
        self.assertTrue(len(floating_ips) == 3, "Count should be 3")
