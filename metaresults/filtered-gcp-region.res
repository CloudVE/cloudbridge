cloudbridge.test.test_region_service.CloudRegionServiceTestCase


Test output
 .....
----------------------------------------------------------------------
Ran 5 tests in 11.722s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 5.60605 s
Function: list at line 390

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   390                                               @dispatch(event="provider.compute.regions.list",
   391                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   392                                               @profile
   393                                               def list(self, limit=None, marker=None):
   394         9         16.0      1.8      0.0          max_result = limit if limit is not None and limit < 500 else 500
   395         9     678185.0  75353.9     12.1          regions_response = (self.provider
   396                                                                           .gcp_compute
   397                                                                           .regions()
   398         9         39.0      4.3      0.0                                  .list(project=self.provider.project_name,
   399         9          8.0      0.9      0.0                                        maxResults=max_result,
   400         9    4925935.0 547326.1     87.9                                        pageToken=marker)
   401                                                                           .execute())
   402         9         29.0      3.2      0.0          regions = [GCPRegion(self.provider, region)
   403         9       1702.0    189.1      0.0                     for region in regions_response['items']]
   404         9         15.0      1.7      0.0          if len(regions) > max_result:
   405                                                       log.warning('Expected at most %d results; got %d',
   406                                                                   max_result, len(regions))
   407         9         12.0      1.3      0.0          return ServerPagedResultList('nextPageToken' in regions_response,
   408         9         14.0      1.6      0.0                                       regions_response.get('nextPageToken'),
   409         9         91.0     10.1      0.0                                       False, data=regions)

Total time: 1.6338 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         3         12.0      4.0      0.0          region = self.provider.get_resource('regions', region_id,
   387         3    1633731.0 544577.0    100.0                                              region=region_id)
   388         3         62.0     20.7      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 1.0209 s
Function: find at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @dispatch(event="provider.compute.regions.find",
   243                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   244                                               @profile
   245                                               def find(self, **kwargs):
   246         3          3.0      1.0      0.0          obj_list = self
   247         3          3.0      1.0      0.0          filters = ['name']
   248         3    1020813.0 340271.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   249         2         78.0     39.0      0.0          return ClientPagedResultList(self._provider, list(matches))

