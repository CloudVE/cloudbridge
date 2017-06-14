import uuid

import azure_integration_test.helpers as helpers


class AzureIntegrationSubnetServiceTestCase(helpers.ProviderTestBase):
    @helpers.skipIfNoService(['network'])
    def test_azure_subnet_service(self):
        subnet_name = '{0}'.format(uuid.uuid4().hex[:6])
        network_name = '{0}'.format(uuid.uuid4().hex[:6])

        subnet_list_before_create = \
            self.provider.network.subnets.list()
        print(str(len(subnet_list_before_create)))

        net = self.provider.network.create(name=network_name)
        net.wait_till_ready()

        self.assertTrue(net is not None, 'Network not created')

        subnet = self.provider.network. \
            subnets.create(network=net, name=subnet_name,
                           cidr_block='10.0.0.0/24')
        self.assertTrue(subnet is not None, 'Subnet not created')

        subnet_id = subnet.id

        subnet_list_after_create = \
            self.provider.network.subnets.list()
        print(str(len(subnet_list_after_create)))

        self.assertTrue(len(subnet_list_after_create),
                        len(subnet_list_before_create) + 1)

        subnet = self.provider.network.subnets.get(subnet_id)
        print("Get Subnet  - " + str(subnet))
        self.assertTrue(
            subnet.name == subnet_name,
            "Subnet name should be {0}".format(subnet_name))

        subnet_list_before_delete = \
            self.provider.network.subnets.list()
        print(str(len(subnet_list_before_delete)))

        subnet.delete()

        subnet_list_after_delete = \
            self.provider.network.subnets.list()
        print(str(len(subnet_list_after_delete)))

        self.assertEqual(len(subnet_list_after_delete),
                         len(subnet_list_before_delete) - 1)

        subnet.delete()
        net.delete()
