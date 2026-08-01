"""
Unit tests for ``AWSVMTypeService`` catalogue retrieval.

AWS has no server-side pagination for VM types, so ``list()`` materialises the
whole catalogue and hands it to ``ClientPagedResultList`` for client-side
paging. Fetching that catalogue is expensive: one
``DescribeInstanceTypeOfferings`` walk plus a ``DescribeInstanceTypes`` call
per 100 types (~14 calls for a real region). Re-fetching it for every page
makes walking the full list quadratic in API calls, so these tests pin the
catalogue down to a single fetch per zone.

Exercised against an in-memory fake connection so they run in CI without
cloud credentials.
"""
import unittest

from cloudbridge.providers.aws import AWSCloudProvider

# Enough types to force several pages at the tests' small result limit, and
# more than one 100-type DescribeInstanceTypes chunk.
CATALOGUE_SIZE = 250
CHUNK_SIZE = 100
PAGE_SIZE = 5


class _FakeEC2Client:
    """Records every catalogue call made against it."""

    def __init__(self, types_by_zone):
        self._types_by_zone = types_by_zone
        self.offering_calls = []          # zone per call
        self.describe_type_calls = []     # list of requested type names

    def describe_instance_type_offerings(self, **kwargs):
        zone = kwargs['Filters'][0]['Values'][0]
        self.offering_calls.append(zone)
        names = self._types_by_zone[zone]
        return {'InstanceTypeOfferings': [{'InstanceType': n} for n in names]}

    def describe_instance_types(self, **kwargs):
        requested = kwargs['InstanceTypes']
        self.describe_type_calls.append(requested)
        return {'InstanceTypes': [{'InstanceType': n,
                                   'CurrentGeneration': True,
                                   'VCpuInfo': {'DefaultVCpus': 2}}
                                  for n in requested]}


class _FakeEC2Conn:
    def __init__(self, client):
        self.meta = type('_Meta', (), {'client': client})()


def _make_provider(zone, types_by_zone):
    provider = AWSCloudProvider({
        'aws_access_key': 'dummy',
        'aws_secret_key': 'dummy',
        'aws_zone_name': zone,
        'default_result_limit': PAGE_SIZE,
    })
    client = _FakeEC2Client(types_by_zone)
    # ec2_conn is a lazily-populated property backed by this attribute.
    provider._ec2_conn = _FakeEC2Conn(client)
    return provider, client


def _zone_types(prefix, count=CATALOGUE_SIZE):
    return ['{0}.type{1}'.format(prefix, i) for i in range(count)]


class AWSVMTypeCatalogueTestCase(unittest.TestCase):

    def setUp(self):
        self.zone = 'us-east-1a'
        self.types = {self.zone: _zone_types('a')}

    def _calls_for_one_catalogue_fetch(self):
        expected_chunks = -(-CATALOGUE_SIZE // CHUNK_SIZE)  # ceil div
        return 1, expected_chunks

    def test_single_list_fetches_catalogue_once(self):
        provider, client = _make_provider(self.zone, self.types)

        provider.compute.vm_types.list()

        offerings, chunks = self._calls_for_one_catalogue_fetch()
        self.assertEqual(len(client.offering_calls), offerings)
        self.assertEqual(len(client.describe_type_calls), chunks)

    def test_repeated_list_calls_reuse_the_catalogue(self):
        provider, client = _make_provider(self.zone, self.types)

        provider.compute.vm_types.list()
        provider.compute.vm_types.list()
        provider.compute.vm_types.list()

        offerings, chunks = self._calls_for_one_catalogue_fetch()
        self.assertEqual(
            len(client.offering_calls), offerings,
            "Catalogue offerings should be fetched once and reused, but were "
            "fetched %s times" % len(client.offering_calls))
        self.assertEqual(
            len(client.describe_type_calls), chunks,
            "Instance type details should be fetched once and reused, but "
            "%s calls were made" % len(client.describe_type_calls))

    def test_paging_through_all_pages_does_not_refetch_catalogue(self):
        """The cost of walking every page must not scale with the page count.

        This is the access pattern used by the standard-behaviour test helper
        (``check_list``) and it is what made the AWS suite take ~50 minutes.
        """
        provider, client = _make_provider(self.zone, self.types)

        result = provider.compute.vm_types.list()
        pages = 1
        while result.is_truncated:
            result = provider.compute.vm_types.list(marker=result.marker)
            pages += 1

        self.assertEqual(pages, -(-CATALOGUE_SIZE // PAGE_SIZE),
                         "Expected to walk the whole catalogue")
        offerings, chunks = self._calls_for_one_catalogue_fetch()
        self.assertEqual(
            len(client.offering_calls), offerings,
            "Walking %s pages refetched the offerings %s times"
            % (pages, len(client.offering_calls)))
        self.assertEqual(
            len(client.describe_type_calls), chunks,
            "Walking %s pages made %s DescribeInstanceTypes calls; the "
            "catalogue should be fetched once"
            % (pages, len(client.describe_type_calls)))

    def test_list_still_returns_the_full_catalogue_contents(self):
        """Caching must not change what callers observe."""
        provider, client = _make_provider(self.zone, self.types)

        seen = []
        result = provider.compute.vm_types.list()
        seen.extend(t.id for t in result)
        while result.is_truncated:
            result = provider.compute.vm_types.list(marker=result.marker)
            seen.extend(t.id for t in result)

        self.assertEqual(seen, self.types[self.zone])

    def test_catalogue_is_keyed_by_zone(self):
        """A provider cloned to another zone must not reuse the first zone's
        catalogue — zones genuinely offer different instance types."""
        other_zone = 'us-east-1b'
        types = {self.zone: _zone_types('a'), other_zone: _zone_types('b')}
        provider, client = _make_provider(self.zone, types)

        first = [t.id for t in provider.compute.vm_types.list()]

        provider.config['aws_zone_name'] = other_zone
        provider._zone_name = other_zone
        second = [t.id for t in provider.compute.vm_types.list()]

        self.assertEqual(first, types[self.zone][:PAGE_SIZE])
        self.assertEqual(second, types[other_zone][:PAGE_SIZE])
        self.assertEqual(client.offering_calls, [self.zone, other_zone])


if __name__ == '__main__':
    unittest.main()
