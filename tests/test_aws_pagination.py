"""
Unit tests for ``BotoEC2Service`` server-side pagination.

``_get_paginated_results`` hands boto3 a ``PaginationConfig`` built from two
separate numbers: ``MaxItems``, how many results the caller asked for, and
``PageSize``, how many the service returns per request. They used to be the
same value, which made a small result limit walk a large scan in tiny
increments - a filtered ``describe_images`` measured 977.6s at a page size of
5 against 10.0s at 1000, for the same single result.

Separating them moves where page boundaries fall, and the resume token
handed back to callers is defined in terms of those boundaries. These tests
pin the round trip: paging a collection with a small limit must still visit
every object exactly once and terminate, whatever the transport page size.

Exercised against moto so they run in CI without cloud credentials.
"""
import unittest

from moto import mock_aws

from cloudbridge.factory import CloudProviderFactory
from cloudbridge.factory import ProviderList
from cloudbridge.providers.aws.helpers import DEFAULT_PAGE_SIZE

# More objects than one page at the result limit below, so paging is forced.
OBJECT_COUNT = 7
RESULT_LIMIT = 2


class AWSPaginationTestCase(unittest.TestCase):

    def setUp(self):
        self.mock = mock_aws()
        self.mock.start()
        self.provider = CloudProviderFactory().create_provider(
            ProviderList.AWS,
            {'aws_access_key': 'a', 'aws_secret_key': 'b',
             'aws_region_name': 'us-east-1',
             'default_result_limit': RESULT_LIMIT})

    def tearDown(self):
        self.mock.stop()

    def _create_volumes(self):
        created = []
        for i in range(OBJECT_COUNT):
            vol = self.provider.storage.volumes.create(
                'cb-page-%d' % i, 1)
            created.append(vol.id)
        return created

    def test_paging_visits_every_object_exactly_once(self):
        expected = self._create_volumes()

        seen = []
        page = self.provider.storage.volumes.list()
        seen.extend(o.id for o in page)
        pages = 1
        while page.is_truncated:
            page = self.provider.storage.volumes.list(marker=page.marker)
            seen.extend(o.id for o in page)
            pages += 1
            self.assertLess(pages, OBJECT_COUNT + 5,
                            "Paging failed to terminate; the resume token is "
                            "probably not advancing.")

        self.assertEqual(sorted(seen), sorted(expected),
                         "Paging must visit every object exactly once.")
        self.assertEqual(len(seen), len(set(seen)),
                         "Paging returned duplicates across pages.")

    def test_a_page_holds_no_more_than_the_result_limit(self):
        # The caller's limit bounds what comes back, independently of how
        # much was fetched per request to produce it.
        self._create_volumes()
        page = self.provider.storage.volumes.list()
        self.assertLessEqual(len(page), RESULT_LIMIT)

    def _page_size(self, list_op):
        # pylint:disable=protected-access
        return self.provider.storage.volumes.svc._page_size(
            self.provider.ec2_conn.meta.client, list_op)

    def test_transport_page_size_is_independent_of_the_result_limit(self):
        # The regression this guards: PageSize tracking the result limit is
        # what made a sparse scan pathological.
        page_size = self._page_size('describe_volumes')
        self.assertEqual(page_size, DEFAULT_PAGE_SIZE)
        self.assertNotEqual(page_size, RESULT_LIMIT)

    def test_page_size_is_clamped_to_the_operations_ceiling(self):
        # DescribeRouteTables allows 100 where most EC2 describes allow more,
        # and exceeding a ceiling is a hard InvalidParameterValue.
        self.assertEqual(self._page_size('describe_route_tables'), 100)

    def test_page_size_survives_an_unknown_operation(self):
        self.assertEqual(self._page_size('not_an_operation'),
                         DEFAULT_PAGE_SIZE)

    def test_configured_page_size_is_used(self):
        self.provider.config['aws_page_size'] = 250
        self.assertEqual(self._page_size('describe_volumes'), 250)

    def test_configured_page_size_is_clamped_to_the_ceiling(self):
        # A configured value is no safer than the default: DescribeRouteTables
        # would reject anything above 100 outright.
        self.provider.config['aws_page_size'] = 900
        self.assertEqual(self._page_size('describe_route_tables'), 100)

    def test_configured_page_size_is_raised_to_the_floor(self):
        # Several EC2 describes require at least 5, so a smaller configured
        # value would be rejected rather than honoured.
        self.provider.config['aws_page_size'] = 1
        self.assertEqual(self._page_size('describe_vpcs'), 5)


if __name__ == "__main__":
    unittest.main()
