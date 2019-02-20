cloudbridge.test.test_vm_types_service.CloudVMTypesServiceTestCase


Test output
 ...
----------------------------------------------------------------------
Ran 3 tests in 13.938s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 12.4638 s
Function: list at line 1095

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1095                                               @dispatch(event="provider.compute.vm_types.list",
  1096                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
  1097                                               @profile
  1098                                               def list(self, limit=None, marker=None):
  1099        40         52.0      1.3      0.0          vm_types = [AzureVMType(self.provider, vm_type)
  1100        40   12459990.0 311499.8    100.0                      for vm_type in self.instance_data]
  1101        40        112.0      2.8      0.0          return ClientPagedResultList(self.provider, vm_types,
  1102        40       3671.0     91.8      0.0                                       limit=limit, marker=marker)

Total time: 1.02121 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         4          5.0      1.2      0.0          obj_list = self
   230         4          2.0      0.5      0.0          filters = ['name']
   231         4    1021106.0 255276.5    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         3         99.0     33.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.609344 s
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222         2          8.0      4.0      0.0          vm_type = (t for t in self if t.id == vm_type_id)
   223         2     609336.0 304668.0    100.0          return next(vm_type, None)

