cloudbridge.test.test_object_life_cycle.CloudObjectLifeCycleTestCase


Test output
 .
----------------------------------------------------------------------
Ran 1 test in 63.726s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 31.713 s
Function: create at line 413

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   413                                               @dispatch(event="provider.storage.volumes.create",
   414                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   415                                               @profile
   416                                               def create(self, label, size, zone, snapshot=None, description=None):
   417         1         12.0     12.0      0.0          AzureVolume.assert_valid_resource_label(label)
   418         1         40.0     40.0      0.0          disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
   419         1          1.0      1.0      0.0          tags = {'Label': label}
   420                                           
   421         1          1.0      1.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   422                                                   snapshot = (self.provider.storage.snapshots.get(snapshot)
   423         1          1.0      1.0      0.0                      if snapshot and isinstance(snapshot, str) else snapshot)
   424                                           
   425         1          1.0      1.0      0.0          if description:
   426                                                       tags.update(Description=description)
   427                                           
   428         1          0.0      0.0      0.0          if snapshot:
   429                                                       params = {
   430                                                           'location':
   431                                                               zone_id or self.provider.azure_client.region_name,
   432                                                           'creation_data': {
   433                                                               'create_option': DiskCreateOption.copy,
   434                                                               'source_uri': snapshot.resource_id
   435                                                           },
   436                                                           'tags': tags
   437                                                       }
   438                                           
   439                                                       disk = self.provider.azure_client.create_snapshot_disk(disk_name,
   440                                                                                                              params)
   441                                           
   442                                                   else:
   443                                                       params = {
   444                                                           'location':
   445         1          1.0      1.0      0.0                      zone_id or self.provider.region_name,
   446         1          0.0      0.0      0.0                  'disk_size_gb': size,
   447                                                           'creation_data': {
   448         1          2.0      2.0      0.0                      'create_option': DiskCreateOption.empty
   449                                                           },
   450         1          1.0      1.0      0.0                  'tags': tags
   451                                                       }
   452                                           
   453         1     416385.0 416385.0      1.3              disk = self.provider.azure_client.create_empty_disk(disk_name,
   454         1   31106427.0 31106427.0     98.1                                                                  params)
   455                                           
   456         1     190049.0 190049.0      0.6          azure_vol = self.provider.azure_client.get_disk(disk.id)
   457         1         64.0     64.0      0.0          cb_vol = AzureVolume(self.provider, azure_vol)
   458                                           
   459         1          1.0      1.0      0.0          return cb_vol

Total time: 30.589 s
Function: delete at line 461

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   461                                               @dispatch(event="provider.storage.volumes.delete",
   462                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   463                                               @profile
   464                                               def delete(self, volume_id):
   465         1          8.0      8.0      0.0          vol_id = (volume_id.id if isinstance(volume_id, AzureVolume)
   466                                                             else volume_id)
   467         1   30589013.0 30589013.0    100.0          self.provider.azure_client.delete_disk(vol_id)

