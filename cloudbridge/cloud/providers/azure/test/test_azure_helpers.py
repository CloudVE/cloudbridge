from cloudbridge.cloud.providers.azure import helpers as azure_helpers
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureHelpersTestCase(ProviderTestBase):
    def test_parse_url_valid(self):
        params = azure_helpers.parse_url('/subscriptionId/{subscriptionId}',
                                         '/subscriptionId/123-1345')
        self.assertTrue(len(params) == 1, 'Parameter count should be 1')

    def test_parse_url_invalid(self):
        with self.assertRaises(Exception):
            azure_helpers.parse_url('/subscriptionId/{subscriptionId}',
                                    '/123-1345')

    def test_filter_matched(self):
        ex1 = Expando()
        ex1.tags = {'Name': 'test'}

        ex2 = Expando()
        ex2.tags = {'Name': 'abc'}

        result = azure_helpers.filter([ex1, ex2], {'Name': 'test'})
        self.assertTrue(len(result) == 1, 'Result count should be one')

    def test_filter_not_matched(self):
        ex1 = Expando()
        ex1.tags = {'Name': 'pqr'}

        ex2 = Expando()
        ex2.tags = {'Name': 'abc'}
        result = azure_helpers.filter([ex1, ex2], {'Name': 'test123'})
        self.assertTrue(len(result) == 0, 'Result count should be zero')

    def test_filter_None(self):
        ex1 = Expando()
        ex1.tags = {'Name': 'test'}

        ex2 = Expando()
        ex2.tags = {'Name': 'abc'}
        result = azure_helpers.filter([ex1, ex2], None)
        self.assertTrue(len(result) == 2, 'Result count should be two')


class Expando(object):
    pass
