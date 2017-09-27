import cloudbridge.cloud.providers.azure.test.helpers as helpers
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureKeyPairServiceTestCase(ProviderTestBase):
    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_create(self):
        key_pair_create = self.provider.security.key_pairs.create('NewKeyPair')
        print("Create Key Pair - " + str(key_pair_create))
        self.assertIsNotNone(key_pair_create)
        self.assertIsNotNone(key_pair_create)
        self.assertIsNotNone(key_pair_create.id)
        self.assertIsNotNone(key_pair_create.material)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_create_Exist(self):
        with self.assertRaises(Exception) as context:
            self.provider.security.key_pairs.create('KeyPair1')
            self.assertTrue(
                'Keypair already exists' in context.exception)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_list(self):
        key_pair_list = self.provider.security.key_pairs.list()
        print("List Key Pairs - " + str(key_pair_list))
        self.assertTrue(key_pair_list.total_results > 0)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_get_exist_and_delete(self):
        keypair_id = 'KeyPair1'
        keypair_get = self.provider.security.key_pairs.get(keypair_id)
        print("Get Key Pair - " + str(keypair_get))
        self.assertIsNotNone(keypair_get)
        keypair_get.delete()

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_get_notExist(self):
        keypair_id = 'KeyPairNotExist'
        keypair_get_not_exist = self.provider.security. \
            key_pairs.get(keypair_id)
        print("Get Key Pair Not Exist - " + str(keypair_get_not_exist))
        self.assertIsNone(keypair_get_not_exist)

    @helpers.skipIfNoService(['security.key_pairs'])
    def test_azure_keypair_find(self):
        keypair_name = 'KeyPair1'
        keypair_find = self.provider.security.key_pairs.find(keypair_name)
        print("Find Key Pair - " + str(keypair_find))
        self.assertTrue(len(keypair_find) > 0)
