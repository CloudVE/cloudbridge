cloudbridge.test.test_region_service.CloudRegionServiceTestCase


Test output
 .....
----------------------------------------------------------------------
Ran 5 tests in 20.301s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 4.47969 s
Function: list at line 908

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   908                                               @dispatch(event="provider.compute.regions.list",
   909                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   910                                               @profile
   911                                               def list(self, limit=None, marker=None):
   912                                                   regions = [
   913        15         26.0      1.7      0.0              AWSRegion(self.provider, region) for region in
   914        15    4477788.0 298519.2    100.0              self.provider.ec2_conn.meta.client.describe_regions()
   915        15       1190.0     79.3      0.0              .get('Regions', [])]
   916        15         28.0      1.9      0.0          return ClientPagedResultList(self.provider, regions,
   917        15        655.0     43.7      0.0                                       limit=limit, marker=marker)

Total time: 1.06103 s
Function: get at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @dispatch(event="provider.compute.regions.get",
   897                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   898                                               @profile
   899                                               def get(self, region_id):
   900         3          8.0      2.7      0.0          log.debug("Getting AWS Region Service with the id: %s",
   901         3         36.0     12.0      0.0                    region_id)
   902         3    1060981.0 353660.3    100.0          region = [r for r in self if r.id == region_id]
   903         3          3.0      1.0      0.0          if region:
   904         2          1.0      0.5      0.0              return region[0]
   905                                                   else:
   906         1          0.0      0.0      0.0              return None

Total time: 0.490871 s
Function: find at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @dispatch(event="provider.compute.regions.find",
   243                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   244                                               @profile
   245                                               def find(self, **kwargs):
   246         3          2.0      0.7      0.0          obj_list = self
   247         3          3.0      1.0      0.0          filters = ['name']
   248         3     490825.0 163608.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   249         2         41.0     20.5      0.0          return ClientPagedResultList(self._provider, list(matches))

