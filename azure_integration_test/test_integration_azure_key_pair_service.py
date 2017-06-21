import uuid

import azure_integration_test.helpers as helpers

from azure_integration_test.helpers import ProviderTestBase


class AzureIntegrationKeyPairServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_key_pair_service(self):

        key_pair_name = '{0}'.format(uuid.uuid4())

        key_pair_create = self.provider.security.key_pairs.\
            create(key_pair_name)
        print(key_pair_create.__dict__)
        self.assertIsNotNone(key_pair_create)

        key_pair_list = self.provider.security.key_pairs.list()
        print(str(key_pair_list))
        self.assertTrue(len(key_pair_list) > 0)

        key_pair_find = self.provider.security.key_pairs.find(key_pair_name)
        print(key_pair_find.__dict__)
        self.assertTrue(len(key_pair_find) > 0)

        key_pair_get = self.provider.security.key_pairs.get(key_pair_name)
        print(key_pair_get.__dict__)
        self.assertIsNotNone(key_pair_get)
