cloudbridge.test.test_object_life_cycle.CloudObjectLifeCycleTestCase


Test output
 .
----------------------------------------------------------------------
Ran 1 test in 11.761s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 9.84804 s
Function: create at line 369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   369                                               @dispatch(event="provider.storage.volumes.create",
   370                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   371                                               @profile
   372                                               def create(self, label, size, zone, snapshot=None, description=None):
   373         1         16.0     16.0      0.0          AWSVolume.assert_valid_resource_label(label)
   374         1          2.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   375         1          0.0      0.0      0.0          snapshot_id = snapshot.id if isinstance(
   376         1          0.0      0.0      0.0              snapshot, AWSSnapshot) and snapshot else snapshot
   377                                           
   378         1         23.0     23.0      0.0          cb_vol = self.svc.create('create_volume', Size=size,
   379         1          0.0      0.0      0.0                                   AvailabilityZone=zone_id,
   380         1    4321521.0 4321521.0     43.9                                   SnapshotId=snapshot_id)
   381                                                   # Wait until ready to tag instance
   382         1    5411356.0 5411356.0     54.9          cb_vol.wait_till_ready()
   383         1     115118.0 115118.0      1.2          cb_vol.label = label
   384         1          1.0      1.0      0.0          if description:
   385                                                       cb_vol.description = description
   386         1          1.0      1.0      0.0          return cb_vol

Total time: 0.400173 s
Function: refresh at line 509

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   509                                               @profile
   510                                               def refresh(self):
   511         5         20.0      4.0      0.0          try:
   512         5     400130.0  80026.0    100.0              self._volume.reload()
   513         5         23.0      4.6      0.0              self._unknown_state = False
   514                                                   except ClientError:
   515                                                       # The volume no longer exists and cannot be refreshed.
   516                                                       # set the status to unknown
   517                                                       self._unknown_state = True

Total time: 0.115102 s
Function: label at line 426

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   426                                               @label.setter
   427                                               # pylint:disable=arguments-differ
   428                                               @profile
   429                                               def label(self, value):
   430         1          8.0      8.0      0.0          self.assert_valid_resource_label(value)
   431         1     115094.0 115094.0    100.0          self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.104595 s
Function: delete at line 388

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   388                                               @dispatch(event="provider.storage.volumes.delete",
   389                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   390                                               @profile
   391                                               def delete(self, vol):
   392         1          2.0      2.0      0.0          volume = vol if isinstance(vol, AWSVolume) else self.get(vol)
   393         1          1.0      1.0      0.0          if volume:
   394                                                       # pylint:disable=protected-access
   395         1     104592.0 104592.0    100.0              volume._volume.delete()

