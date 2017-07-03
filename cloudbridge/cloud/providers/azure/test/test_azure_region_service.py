from cloudbridge.cloud.providers.azure.resources import AzureRegion
from cloudbridge.cloud.providers.azure.test.helpers import ProviderTestBase


class AzureRegionServiceTestCase(ProviderTestBase):
    def test_azure_region_service_list(self):
        regions = self.provider.compute.regions.list()
        self.assertIsNotNone(regions)
        self.assertEqual(
            len(regions), 3)
        print("Region List - " + str(regions))
        for region in regions:
            print(region.id)
            print(region.name)
            print(region.zones)
            self.assertIsInstance(
                region,
                AzureRegion,
                "regions.list() should return a cloudbridge Region")
            self.assertTrue(
                region.name,
                "Region name should be a non-empty string")

    def test_azure_region_service_get(self):
        region_id = "westus2"
        region = self.provider.compute.regions.get(region_id)
        self.assertIsNotNone(region)
        self.assertEqual(region.name, "westus2")
        self.assertEqual(region.zones[0].id, region.id)
        self.assertEqual(region.zones[0].name, region.name)
        self.assertEqual(region.zones[0].region_name, region.name)

    def test_azure_region_service_get_invalid_region_id(self):
        region_id = "invalid"
        region = self.provider.compute.regions.get(region_id)
        self.assertIsNone(region)

    def test_azure_region_service_current(self):
        current_region_name = self.provider.region_name
        print("current region: " + current_region_name)
        region = self.provider.compute.regions.current
        self.assertIsNotNone(region)
        print("Region service returned Region name:" + region.name)
        self.assertEqual(region.name, current_region_name)
