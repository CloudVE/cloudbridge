cloudbridge.test.test_region_service.CloudRegionServiceTestCase


Test output
 .....
----------------------------------------------------------------------
Ran 5 tests in 37.340s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 30.1199 s
Function: list at line 968

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   968                                               @dispatch(event="provider.compute.regions.list",
   969                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   970                                               @profile
   971                                               def list(self, limit=None, marker=None):
   972                                                   # pylint:disable=protected-access
   973        12    8492739.0 707728.2     28.2          if self.provider._keystone_version == 3:
   974        12         51.0      4.2      0.0              os_regions = [OpenStackRegion(self.provider, region)
   975        12   21626556.0 1802213.0     71.8                            for region in self.provider.keystone.regions.list()]
   976        12         50.0      4.2      0.0              return ClientPagedResultList(self.provider, os_regions,
   977        12        502.0     41.8      0.0                                           limit=limit, marker=marker)
   978                                                   else:
   979                                                       # Keystone v3 onwards supports directly listing regions
   980                                                       # but for v2, this convoluted method is necessary.
   981                                                       regions = (
   982                                                           endpoint.get('region') or endpoint.get('region_id')
   983                                                           for svc in self.provider.keystone.service_catalog.get_data()
   984                                                           for endpoint in svc.get('endpoints', [])
   985                                                       )
   986                                                       regions = set(region for region in regions if region)
   987                                                       os_regions = [OpenStackRegion(self.provider, region)
   988                                                                     for region in regions]
   989                                           
   990                                                       return ClientPagedResultList(self.provider, os_regions,
   991                                                                                    limit=limit, marker=marker)

Total time: 6.92382 s
Function: get at line 960

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   960                                               @dispatch(event="provider.compute.regions.get",
   961                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   962                                               @profile
   963                                               def get(self, region_id):
   964         3         33.0     11.0      0.0          log.debug("Getting OpenStack Region with the id: %s", region_id)
   965         3          8.0      2.7      0.0          region = (r for r in self if r.id == region_id)
   966         3    6923783.0 2307927.7    100.0          return next(region, None)

Total time: 2.66103 s
Function: find at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @dispatch(event="provider.compute.regions.find",
   243                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   244                                               @profile
   245                                               def find(self, **kwargs):
   246         3          3.0      1.0      0.0          obj_list = self
   247         3          3.0      1.0      0.0          filters = ['name']
   248         3    2660950.0 886983.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   249         2         72.0     36.0      0.0          return ClientPagedResultList(self._provider, list(matches))

