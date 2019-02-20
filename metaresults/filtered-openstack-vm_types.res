cloudbridge.test.test_vm_types_service.CloudVMTypesServiceTestCase


Test output
 ...
----------------------------------------------------------------------
Ran 3 tests in 46.155s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 15.6285 s
Function: list at line 942

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   942                                               @dispatch(event="provider.compute.vm_types.list",
   943                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   944                                               @profile
   945                                               def list(self, limit=None, marker=None):
   946                                                   cb_itypes = [
   947        17         30.0      1.8      0.0              OpenStackVMType(self.provider, obj)
   948        17    1400787.0  82399.2      9.0              for obj in self.provider.nova.flavors.list(
   949        17        441.0     25.9      0.0                  limit=oshelpers.os_result_limit(self.provider, limit),
   950        17   14226672.0 836863.1     91.0                  marker=marker)]
   951                                           
   952        17        620.0     36.5      0.0          return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)

Total time: 5.54775 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         4          4.0      1.0      0.0          obj_list = self
   230         4          3.0      0.8      0.0          filters = ['name']
   231         4    5547658.0 1386914.5    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         3         86.0     28.7      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 1.84087 s
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222         2          6.0      3.0      0.0          vm_type = (t for t in self if t.id == vm_type_id)
   223         2    1840860.0 920430.0    100.0          return next(vm_type, None)

