from cloudbridge.providers import interfaces
from test.helpers import ProviderTestBase


class ProviderSecurityServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderSecurityServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_list_key_pairs(self):
        key_pairs = self.provider.security.key_pairs.list()
        # Assume there's always one keypair at least
        self.assertIsInstance(key_pairs[0], interfaces.KeyPair)
        self.assertIsNotNone(key_pairs[0].name)

    def test_crud_security_groups(self):
        # groups = self.provider.security.create_security_group()
        groups = self.provider.security.list_security_groups()
        # Assume there's always one keypair at least
#         self.assertIsInstance(groups[0], interfaces.KeyPair)
#         self.assertIsNotNone(key_pairs[0].name)
