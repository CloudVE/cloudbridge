import six

from cloudbridge.cloud.interfaces import Region

from test import helpers
from test.helpers import ProviderTestBase
from test.helpers import standard_interface_tests as sit


class CloudRegionServiceTestCase(ProviderTestBase):

    _multiprocess_can_split_ = True

    @helpers.skipIfNoService(['compute.regions'])
    def test_get_and_list_regions(self):
        """
        Test whether the region listing methods work,
        and whether zones are returned appropriately.
        """
        regions = list(self.provider.compute.regions)
        sit.check_standard_behaviour(
            self, self.provider.compute.regions, regions[-1])

        for region in regions:
            self.assertIsInstance(
                region,
                Region,
                "regions.list() should return a cloudbridge Region")
            self.assertTrue(
                region.name,
                "Region name should be a non-empty string")

    @helpers.skipIfNoService(['compute.regions'])
    def test_regions_unique(self):
        """
        Regions should not return duplicate items
        """
        regions = self.provider.compute.regions.list()
        unique_regions = set([region.id for region in regions])
        self.assertTrue(len(regions) == len(list(unique_regions)))

    @helpers.skipIfNoService(['compute.regions'])
    def test_current_region(self):
        """
        RegionService.current should return a valid region
        """
        current_region = self.provider.compute.regions.current
        self.assertIsInstance(current_region, Region)
        self.assertTrue(current_region in self.provider.compute.regions)

    @helpers.skipIfNoService(['compute.regions'])
    def test_zones(self):
        """
        Test whether regions return the correct zone information
        """
        zone_find_count = 0
        test_zone = helpers.get_provider_test_data(self.provider, "placement")
        for region in self.provider.compute.regions:
            self.assertTrue(region.name)
            for zone in region.zones:
                self.assertTrue(zone.id)
                self.assertTrue(zone.name)
                self.assertTrue(zone.region_name is None or
                                isinstance(zone.region_name,
                                           six.string_types))
                if test_zone == zone.name:
                    zone_find_count += 1
        # zone info cannot be repeated between regions
        self.assertEqual(zone_find_count, 1)
