cloudbridge.test.test_region_service.CloudRegionServiceTestCase


Test output
 .....
----------------------------------------------------------------------
Ran 5 tests in 5.234s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 3.0634 s
Function: list at line 1120

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1120                                               @dispatch(event="provider.compute.regions.list",
  1121                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1122                                               @profile
  1123                                               def list(self, limit=None, marker=None):
  1124        14         24.0      1.7      0.0          regions = [AzureRegion(self.provider, region)
  1125        14    3062696.0 218764.0    100.0                     for region in self.provider.azure_client.list_locations()]
  1126        14         48.0      3.4      0.0          return ClientPagedResultList(self.provider, regions,
  1127        14        628.0     44.9      0.0                                       limit=limit, marker=marker)

Total time: 0.913141 s
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113         3          5.0      1.7      0.0          region = None
  1114        64     912968.0  14265.1    100.0          for azureRegion in self.provider.azure_client.list_locations():
  1115        63         39.0      0.6      0.0              if azureRegion.name == region_id:
  1116         2         67.0     33.5      0.0                  region = AzureRegion(self.provider, azureRegion)
  1117         2         61.0     30.5      0.0                  break
  1118         3          1.0      0.3      0.0          return region

Total time: 0.30175 s
Function: find at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @dispatch(event="provider.compute.regions.find",
   243                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   244                                               @profile
   245                                               def find(self, **kwargs):
   246         3          3.0      1.0      0.0          obj_list = self
   247         3          3.0      1.0      0.0          filters = ['name']
   248         3     301689.0 100563.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   249         2         55.0     27.5      0.0          return ClientPagedResultList(self._provider, list(matches))

