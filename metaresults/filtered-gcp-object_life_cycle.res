cloudbridge.test.test_object_life_cycle.CloudObjectLifeCycleTestCase


Test output
 .
----------------------------------------------------------------------
Ran 1 test in 5.476s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 2.06655 s
Function: create at line 1269

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1269                                               @dispatch(event="provider.storage.volumes.create",
  1270                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1271                                               @profile
  1272                                               def create(self, label, size, zone, snapshot=None, description=None):
  1273         1         11.0     11.0      0.0          GCPVolume.assert_valid_resource_label(label)
  1274         1         36.0     36.0      0.0          name = GCPVolume._generate_name_from_label(label, 'cb-vol')
  1275         1          2.0      2.0      0.0          if not isinstance(zone, GCPPlacementZone):
  1276         1          3.0      3.0      0.0              zone = GCPPlacementZone(
  1277         1          2.0      2.0      0.0                  self.provider,
  1278         1     841996.0 841996.0     40.7                  self.provider.get_resource('zones', zone))
  1279         1          6.0      6.0      0.0          zone_name = zone.name
  1280         1          1.0      1.0      0.0          snapshot_id = snapshot.id if isinstance(
  1281         1          3.0      3.0      0.0              snapshot, GCPSnapshot) and snapshot else snapshot
  1282         1          2.0      2.0      0.0          labels = {'cblabel': label}
  1283         1          1.0      1.0      0.0          if description:
  1284                                                       labels['description'] = description
  1285                                                   disk_body = {
  1286         1          2.0      2.0      0.0              'name': name,
  1287         1          1.0      1.0      0.0              'sizeGb': size,
  1288         1          5.0      5.0      0.0              'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
  1289         1          1.0      1.0      0.0              'sourceSnapshot': snapshot_id,
  1290         1          2.0      2.0      0.0              'labels': labels
  1291                                                   }
  1292         1      14188.0  14188.0      0.7          operation = (self.provider
  1293                                                                    .gcp_compute
  1294                                                                    .disks()
  1295                                                                    .insert(
  1296         1          1.0      1.0      0.0                               project=self._provider.project_name,
  1297         1          1.0      1.0      0.0                               zone=zone_name,
  1298         1     800621.0 800621.0     38.7                               body=disk_body)
  1299                                                                    .execute())
  1300         1     409666.0 409666.0     19.8          cb_vol = self.get(operation.get('targetLink'))
  1301         1          1.0      1.0      0.0          return cb_vol

Total time: 0.796799 s
Function: delete at line 1303

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1303                                               @dispatch(event="provider.storage.volumes.delete",
  1304                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1305                                               @profile
  1306                                               def delete(self, volume):
  1307         1          2.0      2.0      0.0          volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
  1308         1          1.0      1.0      0.0          if volume:
  1309         1       8522.0   8522.0      1.1              (self._provider.gcp_compute
  1310                                                                      .disks()
  1311         1          3.0      3.0      0.0                             .delete(project=self.provider.project_name,
  1312         1        445.0    445.0      0.1                                     zone=volume.zone_name,
  1313         1     787826.0 787826.0     98.9                                     disk=volume.name)
  1314                                                                      .execute())

Total time: 0.6109 s
Function: get at line 1196

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1196                                               @dispatch(event="provider.storage.volumes.get",
  1197                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1198                                               @profile
  1199                                               def get(self, volume_id):
  1200         2     610859.0 305429.5    100.0          vol = self.provider.get_resource('disks', volume_id)
  1201         2         41.0     20.5      0.0          return GCPVolume(self.provider, vol) if vol else None

Total time: 0.243625 s
Function: refresh at line 1789

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1789                                               @profile
  1790                                               def refresh(self):
  1791                                                   """
  1792                                                   Refreshes the state of this volume by re-querying the cloud provider
  1793                                                   for its latest state.
  1794                                                   """
  1795         1     243620.0 243620.0    100.0          vol = self._provider.storage.volumes.get(self.id)
  1796         1          2.0      2.0      0.0          if vol:
  1797                                                       # pylint:disable=protected-access
  1798         1          3.0      3.0      0.0              self._volume = vol._volume
  1799                                                   else:
  1800                                                       # volume no longer exists
  1801                                                       self._volume['status'] = VolumeState.UNKNOWN

