import itertools

from cloudbridge.cloud.interfaces import Region
from test.helpers import ProviderTestBase


class CloudRegionServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(CloudRegionServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_get_and_list_regions(self):
        """
        Test whether the region listing methods work,
        and whether zones are returned appropriately.
        """
        regions = self.provider.compute.regions.list()

        # check iteration
        iter_regions = list(itertools.islice(
            self.provider.compute.regions,
            len(regions)))
        self.assertListEqual(iter_regions, regions)

        for region in regions:
            self.assertIsInstance(
                region,
                Region,
                "regions.list() should return a cloudbridge Region")
            self.assertTrue(
                region.name,
                "Region name should be a non-empty string")

        region = self.provider.compute.regions.get(regions[0].id)
        self.assertEqual(
            region,
            regions[0],
            "List and get methods should return the same regions")

        self.assertTrue(
            region.id in repr(region),
            "repr(obj) should contain the object id so that the object"
            " can be reconstructed, but does not.")
