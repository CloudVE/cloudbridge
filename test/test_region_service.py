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
        iter_regions = list(self.provider.compute.regions)
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

        self.assertTrue(
            region.name in region.to_json(),
            "Region name {0} not in JSON representation {1}".format(
                region.name, region.to_json()))

    def test_regions_unique(self):
        """
        Regions should not return duplicate items
        """
        regions = self.provider.compute.regions.list()
        unique_regions = set([region.id for region in regions])
        self.assertTrue(len(regions) == len(list(unique_regions)))
