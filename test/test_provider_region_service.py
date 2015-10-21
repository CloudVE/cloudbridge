from cloudbridge.providers.interfaces import Region
from test.helpers import ProviderTestBase


class ProviderRegionServiceTestCase(ProviderTestBase):

    def __init__(self, methodName, provider):
        super(ProviderRegionServiceTestCase, self).__init__(
            methodName=methodName, provider=provider)

    def test_get_and_list_regions(self):
        """
        Test whether the region listing methods work,
        and whether zones are returned appropriately.
        """
        regions = self.provider.compute.regions.list()
        for region in regions:
            self.assertIsInstance(
                region,
                Region,
                "regions.list() should return a cloudbridge Region")

        region = self.provider.compute.regions.get(regions[0].name)
        self.assertEqual(
            region,
            regions[0],
            "List and get methods should return the same regions")
