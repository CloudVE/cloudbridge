cloudbridge.test.test_object_life_cycle.CloudObjectLifeCycleTestCase


Test output
 .
----------------------------------------------------------------------
Ran 1 test in 5.859s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 2.18261 s
Function: create at line 427

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   427                                               @dispatch(event="provider.storage.volumes.create",
   428                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   429                                               @profile
   430                                               def create(self, label, size, zone, snapshot=None, description=None):
   431         1         12.0     12.0      0.0          OpenStackVolume.assert_valid_resource_label(label)
   432         1          2.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   433         1          1.0      1.0      0.0          snapshot_id = snapshot.id if isinstance(
   434         1          1.0      1.0      0.0              snapshot, OpenStackSnapshot) and snapshot else snapshot
   435                                           
   436         1     884819.0 884819.0     40.5          os_vol = self.provider.cinder.volumes.create(
   437         1          1.0      1.0      0.0              size, name=label, description=description,
   438         1    1297753.0 1297753.0     59.5              availability_zone=zone_id, snapshot_id=snapshot_id)
   439         1         21.0     21.0      0.0          return OpenStackVolume(self.provider, os_vol)

Total time: 0.726248 s
Function: refresh at line 662

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   662                                               @profile
   663                                               def refresh(self):
   664                                                   """
   665                                                   Refreshes the state of this volume by re-querying the cloud provider
   666                                                   for its latest state.
   667                                                   """
   668         1         24.0     24.0      0.0          vol = self._provider.storage.volumes.get(
   669         1     726215.0 726215.0    100.0              self.id)
   670         1          2.0      2.0      0.0          if vol:
   671                                                       # pylint:disable=protected-access
   672         1          7.0      7.0      0.0              self._volume = vol._volume  # pylint:disable=protected-access
   673                                                   else:
   674                                                       # The volume no longer exists and cannot be refreshed.
   675                                                       # set the status to unknown
   676                                                       self._volume.status = 'unknown'

Total time: 0.683317 s
Function: get at line 381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   381                                               @dispatch(event="provider.storage.volumes.get",
   382                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   383                                               @profile
   384                                               def get(self, volume_id):
   385         1          1.0      1.0      0.0          try:
   386         1          0.0      0.0      0.0              return OpenStackVolume(
   387         1     683316.0 683316.0    100.0                  self.provider, self.provider.cinder.volumes.get(volume_id))
   388                                                   except CinderNotFound:
   389                                                       log.debug("Volume %s was not found.", volume_id)
   390                                                       return None

Total time: 0.582492 s
Function: delete at line 441

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   441                                               @dispatch(event="provider.storage.volumes.delete",
   442                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   443                                               @profile
   444                                               def delete(self, volume):
   445         1          2.0      2.0      0.0          volume = (volume if isinstance(volume, OpenStackVolume)
   446                                                             else self.get(volume))
   447         1          1.0      1.0      0.0          if volume:
   448                                                       # pylint:disable=protected-access
   449         1     582489.0 582489.0    100.0              volume._volume.delete()

