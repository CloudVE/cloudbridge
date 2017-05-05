from azure_test.helpers import ProviderTestBase


class AzureProviderTestCase(ProviderTestBase):
    def test_azure_provider(self):
        compute = self.provider.compute
        self.assertTrue(compute is not None, 'Compute should not be None')

        self.assertTrue(compute.images is not None,
                        'Images should not be none')

        with self.assertRaises(NotImplementedError):
            self.assertTrue(compute.instances is not None,
                            'Instances should not be none')

        with self.assertRaises(NotImplementedError):
            self.assertTrue(compute.instance_types is not None,
                            'Instance types should not be none')

        with self.assertRaises(NotImplementedError):
            self.assertTrue(compute.regions is not None,
                            'Regions should not be none')

        with self.assertRaises(Exception):
            network = self.provider.network
            self.assertTrue(network is not None, 'Network should not be None')

        block_store = self.provider.block_store
        self.assertTrue(block_store is not None,
                        'Block Store should not be None')

        block_store = self.provider.block_store
        self.assertTrue(block_store is not None,
                        'Block Store should not be None')

        object_store = self.provider.object_store
        self.assertTrue(object_store is not None,
                        'Object Store should not be None')

        security = self.provider.security
        self.assertTrue(security is not None, 'Security should not be None')
