"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.

Use ``nose tests`` to run these unit tests.
"""
import unittest
from cloudbridge.providers.factory import CloudProviderFactory
from cloudbridge.providers.factory import ProviderList
from cloudbridge.providers import interfaces


class TestProviderSecurityService(unittest.TestCase):

    def setUp(self):
        config = {}
        self.provider = CloudProviderFactory().create_provider(ProviderList.EC2, config)

    def test_list_key_pairs(self):
        key_pairs = self.provider.security.list_key_pairs()
        # Assume there's always one keypair at least
        self.assertIsInstance(key_pairs[0], interfaces.KeyPair)
        self.assertIsNotNone(key_pairs[0].name)
