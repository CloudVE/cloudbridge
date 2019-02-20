cloudbridge.test.test_vm_types_service.CloudVMTypesServiceTestCase


Test output
 ...
----------------------------------------------------------------------
Ran 3 tests in 2.759s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 1.1765 s
Function: list at line 881

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   881                                               @dispatch(event="provider.compute.vm_types.list",
   882                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   883                                               @profile
   884                                               def list(self, limit=None, marker=None):
   885        41         40.0      1.0      0.0          vm_types = [AWSVMType(self.provider, vm_type)
   886        41    1172609.0  28600.2     99.7                      for vm_type in self.instance_data]
   887        41         54.0      1.3      0.0          return ClientPagedResultList(self.provider, vm_types,
   888        41       3799.0     92.7      0.3                                       limit=limit, marker=marker)

Total time: 0.572682 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         4          3.0      0.8      0.0          obj_list = self
   230         4          0.0      0.0      0.0          filters = ['name']
   231         4     572609.0 143152.2    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         3         70.0     23.3      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.001541 s
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222         2          3.0      1.5      0.2          vm_type = (t for t in self if t.id == vm_type_id)
   223         2       1538.0    769.0     99.8          return next(vm_type, None)

