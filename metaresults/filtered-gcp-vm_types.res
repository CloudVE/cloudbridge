cloudbridge.test.test_vm_types_service.CloudVMTypesServiceTestCase


Test output
 ...
----------------------------------------------------------------------
Ran 3 tests in 4.855s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 2.04614 s
Function: list at line 367

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   367                                               @dispatch(event="provider.compute.vm_types.list",
   368                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   369                                               @profile
   370                                               def list(self, limit=None, marker=None):
   371         9         20.0      2.2      0.0          inst_types = [GCPVMType(self.provider, inst_type)
   372         9    2045492.0 227276.9    100.0                        for inst_type in self.instance_data]
   373         9         31.0      3.4      0.0          return ClientPagedResultList(self.provider, inst_types,
   374         9        596.0     66.2      0.0                                       limit=limit, marker=marker)

Total time: 1.11624 s
Function: find at line 348

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   348                                               @dispatch(event="provider.compute.vm_types.find",
   349                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   350                                               @profile
   351                                               def find(self, **kwargs):
   352         4          5.0      1.2      0.0          matched_inst_types = []
   353        88    1115278.0  12673.6     99.9          for inst_type in self.instance_data:
   354        85         75.0      0.9      0.0              is_match = True
   355        87        296.0      3.4      0.0              for key, value in kwargs.items():
   356        85         71.0      0.8      0.0                  if key not in inst_type:
   357         1          1.0      1.0      0.0                      raise InvalidParamException(
   358         1         28.0     28.0      0.0                          "Unrecognised parameters for search: %s." % key)
   359        84         90.0      1.1      0.0                  if inst_type.get(key) != value:
   360        82         53.0      0.6      0.0                      is_match = False
   361        82        231.0      2.8      0.0                      break
   362        84         66.0      0.8      0.0              if is_match:
   363         2          2.0      1.0      0.0                  matched_inst_types.append(
   364         2         40.0     20.0      0.0                      GCPVMType(self.provider, inst_type))
   365         3          3.0      1.0      0.0          return matched_inst_types

Total time: 0.536744 s
Function: get at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @dispatch(event="provider.compute.vm_types.get",
   342                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   343                                               @profile
   344                                               def get(self, vm_type_id):
   345         2     536721.0 268360.5    100.0          vm_type = self.provider.get_resource('machineTypes', vm_type_id)
   346         2         23.0     11.5      0.0          return GCPVMType(self.provider, vm_type) if vm_type else None

