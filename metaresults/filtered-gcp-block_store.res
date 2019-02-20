cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase


Test output
 ......
----------------------------------------------------------------------
Ran 6 tests in 565.821s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 99.9525 s
Function: create at line 490

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   490                                               @dispatch(event="provider.compute.instances.create",
   491                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   492                                               @profile
   493                                               def create(self, label, image, vm_type, subnet, zone=None,
   494                                                          key_pair=None, vm_firewalls=None, user_data=None,
   495                                                          launch_config=None, **kwargs):
   496                                                   """
   497                                                   Creates a new virtual machine instance.
   498                                                   """
   499         2         24.0     12.0      0.0          GCPInstance.assert_valid_resource_name(label)
   500         2          9.0      4.5      0.0          zone_name = self.provider.default_zone
   501         2          4.0      2.0      0.0          if zone:
   502         2          6.0      3.0      0.0              if not isinstance(zone, GCPPlacementZone):
   503         2          3.0      1.5      0.0                  zone = GCPPlacementZone(
   504         2          4.0      2.0      0.0                      self.provider,
   505         2     318278.0 159139.0      0.3                      self.provider.get_resource('zones', zone))
   506         2         11.0      5.5      0.0              zone_name = zone.name
   507         2          8.0      4.0      0.0          if not isinstance(vm_type, GCPVMType):
   508         2     514841.0 257420.5      0.5              vm_type = self.provider.compute.vm_types.get(vm_type)
   509                                           
   510         2          5.0      2.5      0.0          network_interface = {'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
   511         2          7.0      3.5      0.0                                                  'name': 'External NAT'}]}
   512         2          5.0      2.5      0.0          if subnet:
   513         2         10.0      5.0      0.0              network_interface['subnetwork'] = subnet.id
   514                                                   else:
   515                                                       network_interface['network'] = 'global/networks/default'
   516                                           
   517         2          5.0      2.5      0.0          num_roots = 0
   518         2          4.0      2.0      0.0          disks = []
   519         2          5.0      2.5      0.0          boot_disk = None
   520         2          8.0      4.0      0.0          if isinstance(launch_config, GCPLaunchConfig):
   521                                                       for disk in launch_config.block_devices:
   522                                                           if not disk.source:
   523                                                               volume_name = 'disk-{0}'.format(uuid.uuid4())
   524                                                               volume_size = disk.size if disk.size else 1
   525                                                               volume = self.provider.storage.volumes.create(
   526                                                                   volume_name, volume_size, zone)
   527                                                               volume.wait_till_ready()
   528                                                               source_field = 'source'
   529                                                               source_value = volume.id
   530                                                           elif isinstance(disk.source, GCPMachineImage):
   531                                                               source_field = 'initializeParams'
   532                                                               # Explicitly set diskName; otherwise, instance label will
   533                                                               # be used by default which may collide with existing disks.
   534                                                               source_value = {
   535                                                                   'sourceImage': disk.source.id,
   536                                                                   'diskName': 'image-disk-{0}'.format(uuid.uuid4()),
   537                                                                   'diskSizeGb': disk.size if disk.size else 20}
   538                                                           elif isinstance(disk.source, GCPVolume):
   539                                                               source_field = 'source'
   540                                                               source_value = disk.source.id
   541                                                           elif isinstance(disk.source, GCPSnapshot):
   542                                                               volume = disk.source.create_volume(zone, size=disk.size)
   543                                                               volume.wait_till_ready()
   544                                                               source_field = 'source'
   545                                                               source_value = volume.id
   546                                                           else:
   547                                                               log.warning('Unknown disk source')
   548                                                               continue
   549                                                           autoDelete = True
   550                                                           if disk.delete_on_terminate is not None:
   551                                                               autoDelete = disk.delete_on_terminate
   552                                                           num_roots += 1 if disk.is_root else 0
   553                                                           if disk.is_root and not boot_disk:
   554                                                               boot_disk = {'boot': True,
   555                                                                            'autoDelete': autoDelete,
   556                                                                            source_field: source_value}
   557                                                           else:
   558                                                               disks.append({'boot': False,
   559                                                                             'autoDelete': autoDelete,
   560                                                                             source_field: source_value})
   561                                           
   562         2          4.0      2.0      0.0          if num_roots > 1:
   563                                                       log.warning('The launch config contains %d boot disks. Will '
   564                                                                   'use the first one', num_roots)
   565         2          4.0      2.0      0.0          if image:
   566         2          5.0      2.5      0.0              if boot_disk:
   567                                                           log.warning('A boot image is given while the launch config '
   568                                                                       'contains a boot disk, too. The launch config '
   569                                                                       'will be used.')
   570                                                       else:
   571         2          6.0      3.0      0.0                  if not isinstance(image, GCPMachineImage):
   572         2     350599.0 175299.5      0.4                      image = self.provider.compute.images.get(image)
   573                                                           # Explicitly set diskName; otherwise, instance name will be
   574                                                           # used by default which may conflict with existing disks.
   575                                                           boot_disk = {
   576         2          4.0      2.0      0.0                      'boot': True,
   577         2          4.0      2.0      0.0                      'autoDelete': True,
   578                                                               'initializeParams': {
   579         2          9.0      4.5      0.0                          'sourceImage': image.id,
   580         2        112.0     56.0      0.0                          'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}
   581                                           
   582         2          5.0      2.5      0.0          if not boot_disk:
   583                                                       log.warning('No boot disk is given for instance %s.', label)
   584                                                       return None
   585                                                   # The boot disk must be the first disk attached to the instance.
   586         2          6.0      3.0      0.0          disks.insert(0, boot_disk)
   587                                           
   588                                                   config = {
   589         2         90.0     45.0      0.0              'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
   590         2         10.0      5.0      0.0              'machineType': vm_type.resource_url,
   591         2          5.0      2.5      0.0              'disks': disks,
   592         2          7.0      3.5      0.0              'networkInterfaces': [network_interface]
   593                                                   }
   594                                           
   595         2          5.0      2.5      0.0          if vm_firewalls and isinstance(vm_firewalls, list):
   596                                                       vm_firewall_names = []
   597                                                       if isinstance(vm_firewalls[0], VMFirewall):
   598                                                           vm_firewall_names = [f.name for f in vm_firewalls]
   599                                                       elif isinstance(vm_firewalls[0], str):
   600                                                           vm_firewall_names = vm_firewalls
   601                                                       if len(vm_firewall_names) > 0:
   602                                                           config['tags'] = {}
   603                                                           config['tags']['items'] = vm_firewall_names
   604                                           
   605         2          4.0      2.0      0.0          if user_data:
   606                                                       entry = {'key': 'user-data', 'value': user_data}
   607                                                       config['metadata'] = {'items': [entry]}
   608                                           
   609         2          4.0      2.0      0.0          if key_pair:
   610                                                       if not isinstance(key_pair, GCPKeyPair):
   611                                                           key_pair = self._provider.security.key_pairs.get(key_pair)
   612                                                       if key_pair:
   613                                                           kp = key_pair._key_pair
   614                                                           kp_entry = {
   615                                                               "key": "ssh-keys",
   616                                                               # Format is not removed from public key portion
   617                                                               "value": "{}:{} {}".format(
   618                                                                   self.provider.vm_default_user_name,
   619                                                                   kp.public_key,
   620                                                                   kp.name)
   621                                                               }
   622                                                           meta = config.get('metadata', {})
   623                                                           if meta:
   624                                                               items = meta.get('items', [])
   625                                                               items.append(kp_entry)
   626                                                           else:
   627                                                               config['metadata'] = {'items': [kp_entry]}
   628                                           
   629         2          6.0      3.0      0.0          config['labels'] = {'cblabel': label}
   630                                           
   631         2      53732.0  26866.0      0.1          operation = (self.provider
   632                                                                    .gcp_compute.instances()
   633         2         25.0     12.5      0.0                           .insert(project=self.provider.project_name,
   634         2          3.0      1.5      0.0                                   zone=zone_name,
   635         2    2888642.0 1444321.0      2.9                                   body=config)
   636                                                                    .execute())
   637         2          6.0      3.0      0.0          instance_id = operation.get('targetLink')
   638         2   95100637.0 47550318.5     95.1          self.provider.wait_for_operation(operation, zone=zone_name)
   639         2     725357.0 362678.5      0.7          cb_inst = self.get(instance_id)
   640         2          6.0      3.0      0.0          return cb_inst

Total time: 71.0745 s
Function: get at line 642

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   642                                               @dispatch(event="provider.compute.instances.get",
   643                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   644                                               @profile
   645                                               def get(self, instance_id):
   646                                                   """
   647                                                   Returns an instance given its name. Returns None
   648                                                   if the object does not exist.
   649                                           
   650                                                   A GCP instance is uniquely identified by its selfLink, which is used
   651                                                   as its id.
   652                                                   """
   653       223   71070584.0 318702.2    100.0          instance = self.provider.get_resource('instances', instance_id)
   654       223       3960.0     17.8      0.0          return GCPInstance(self.provider, instance) if instance else None

Total time: 70.4152 s
Function: refresh at line 1237

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1237                                               @profile
  1238                                               def refresh(self):
  1239                                                   """
  1240                                                   Refreshes the state of this instance by re-querying the cloud provider
  1241                                                   for its latest state.
  1242                                                   """
  1243       221   70413139.0 318611.5    100.0          inst = self._provider.compute.instances.get(self.id)
  1244       221        245.0      1.1      0.0          if inst:
  1245                                                       # pylint:disable=protected-access
  1246       219       1786.0      8.2      0.0              self._gcp_instance = inst._gcp_instance
  1247                                                   else:
  1248                                                       # instance no longer exists
  1249         2          7.0      3.5      0.0              self._gcp_instance['status'] = InstanceState.UNKNOWN

Total time: 36.8745 s
Function: create at line 1381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1381                                               @dispatch(event="provider.storage.snapshots.create",
  1382                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1383                                               @profile
  1384                                               def create(self, label, volume, description=None):
  1385        23        402.0     17.5      0.0          GCPSnapshot.assert_valid_resource_label(label)
  1386         3        142.0     47.3      0.0          name = GCPSnapshot._generate_name_from_label(label, 'cbsnap')
  1387         3         34.0     11.3      0.0          volume_name = volume.name if isinstance(volume, GCPVolume) else volume
  1388         3          5.0      1.7      0.0          labels = {'cblabel': label}
  1389         3          3.0      1.0      0.0          if description:
  1390         3          3.0      1.0      0.0              labels['description'] = description
  1391                                                   snapshot_body = {
  1392         3          3.0      1.0      0.0              "name": name,
  1393         3          5.0      1.7      0.0              "labels": labels
  1394                                                   }
  1395         3      23933.0   7977.7      0.1          operation = (self.provider
  1396                                                                    .gcp_compute
  1397                                                                    .disks()
  1398                                                                    .createSnapshot(
  1399         3         11.0      3.7      0.0                               project=self.provider.project_name,
  1400         3          3.0      1.0      0.0                               zone=self.provider.default_zone,
  1401         3    2639496.0 879832.0      7.2                               disk=volume_name, body=snapshot_body)
  1402                                                                    .execute())
  1403         3          6.0      2.0      0.0          if 'zone' not in operation:
  1404                                                       return None
  1405         3         13.0      4.3      0.0          self.provider.wait_for_operation(operation,
  1406         3   33567626.0 11189208.7     91.0                                           zone=self.provider.default_zone)
  1407         3     642794.0 214264.7      1.7          cb_snap = self.get(name)
  1408         3          3.0      1.0      0.0          return cb_snap

Total time: 20.4031 s
Function: get at line 1196

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1196                                               @dispatch(event="provider.storage.volumes.get",
  1197                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1198                                               @profile
  1199                                               def get(self, volume_id):
  1200        66   20402097.0 309122.7    100.0          vol = self.provider.get_resource('disks', volume_id)
  1201        66        985.0     14.9      0.0          return GCPVolume(self.provider, vol) if vol else None

Total time: 17.8227 s
Function: refresh at line 1789

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1789                                               @profile
  1790                                               def refresh(self):
  1791                                                   """
  1792                                                   Refreshes the state of this volume by re-querying the cloud provider
  1793                                                   for its latest state.
  1794                                                   """
  1795        57   17822428.0 312674.2    100.0          vol = self._provider.storage.volumes.get(self.id)
  1796        57         59.0      1.0      0.0          if vol:
  1797                                                       # pylint:disable=protected-access
  1798        55        189.0      3.4      0.0              self._volume = vol._volume
  1799                                                   else:
  1800                                                       # volume no longer exists
  1801         2          7.0      3.5      0.0              self._volume['status'] = VolumeState.UNKNOWN

Total time: 9.97485 s
Function: create at line 1269

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1269                                               @dispatch(event="provider.storage.volumes.create",
  1270                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1271                                               @profile
  1272                                               def create(self, label, size, zone, snapshot=None, description=None):
  1273        16        175.0     10.9      0.0          GCPVolume.assert_valid_resource_label(label)
  1274         6        268.0     44.7      0.0          name = GCPVolume._generate_name_from_label(label, 'cb-vol')
  1275         6         12.0      2.0      0.0          if not isinstance(zone, GCPPlacementZone):
  1276         6          5.0      0.8      0.0              zone = GCPPlacementZone(
  1277         6         12.0      2.0      0.0                  self.provider,
  1278         6    2128729.0 354788.2     21.3                  self.provider.get_resource('zones', zone))
  1279         6         26.0      4.3      0.0          zone_name = zone.name
  1280         6          8.0      1.3      0.0          snapshot_id = snapshot.id if isinstance(
  1281         6         16.0      2.7      0.0              snapshot, GCPSnapshot) and snapshot else snapshot
  1282         6          9.0      1.5      0.0          labels = {'cblabel': label}
  1283         6          5.0      0.8      0.0          if description:
  1284         1          1.0      1.0      0.0              labels['description'] = description
  1285                                                   disk_body = {
  1286         6          5.0      0.8      0.0              'name': name,
  1287         6          4.0      0.7      0.0              'sizeGb': size,
  1288         6         25.0      4.2      0.0              'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
  1289         6          6.0      1.0      0.0              'sourceSnapshot': snapshot_id,
  1290         6          9.0      1.5      0.0              'labels': labels
  1291                                                   }
  1292         6      70259.0  11709.8      0.7          operation = (self.provider
  1293                                                                    .gcp_compute
  1294                                                                    .disks()
  1295                                                                    .insert(
  1296         6         17.0      2.8      0.0                               project=self._provider.project_name,
  1297         6          3.0      0.5      0.0                               zone=zone_name,
  1298         6    5914209.0 985701.5     59.3                               body=disk_body)
  1299                                                                    .execute())
  1300         6    1861043.0 310173.8     18.7          cb_vol = self.get(operation.get('targetLink'))
  1301         6          7.0      1.2      0.0          return cb_vol

Total time: 8.58669 s
Function: get_or_create_default at line 1098

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1098                                               @profile
  1099                                               def get_or_create_default(self, zone):
  1100                                                   """
  1101                                                   Return an existing or create a new subnet for the supplied zone.
  1102                                           
  1103                                                   In GCP, subnets are a regional resource so a single subnet can services
  1104                                                   an entire region. The supplied zone parameter is used to derive the
  1105                                                   parent region under which the default subnet then exists.
  1106                                                   """
  1107                                                   # In case the supplied zone param is `None`, resort to the default one
  1108         2          7.0      3.5      0.0          region = self._zone_to_region(zone or self.provider.default_zone,
  1109         2    1809305.0 904652.5     21.1                                        return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111         2    6777361.0 3388680.5     78.9          for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112         2         14.0      7.0      0.0              if sn.region == region.id:
  1113         2          5.0      2.5      0.0                  return sn
  1114                                                   # No default subnet in the supplied zone. Look for a default network,
  1115                                                   # then create a subnet whose address space does not overlap with any
  1116                                                   # other existing subnets. If there are existing subnets, this process
  1117                                                   # largely assumes the subnet address spaces are contiguous when it
  1118                                                   # does the calculations (e.g., 10.0.0.0/24, 10.0.1.0/24).
  1119                                                   cidr_block = GCPSubnet.CB_DEFAULT_SUBNET_IPV4RANGE
  1120                                                   net = self.provider.networking.networks.get_or_create_default()
  1121                                                   if net.subnets:
  1122                                                       max_sn = net.subnets[0]
  1123                                                       # Find the maximum address subnet address space within the network
  1124                                                       for esn in net.subnets:
  1125                                                           if (ipaddress.ip_network(esn.cidr_block) >
  1126                                                                   ipaddress.ip_network(max_sn.cidr_block)):
  1127                                                               max_sn = esn
  1128                                                       max_sn_ipa = ipaddress.ip_network(max_sn.cidr_block)
  1129                                                       # Find the next available subnet after the max one, based on the
  1130                                                       # max subnet size
  1131                                                       next_sn_address = (
  1132                                                           next(max_sn_ipa.hosts()) + max_sn_ipa.num_addresses - 1)
  1133                                                       cidr_block = "{}/{}".format(next_sn_address, max_sn_ipa.prefixlen)
  1134                                                   sn = self.provider.networking.subnets.create(
  1135                                                           label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL,
  1136                                                           cidr_block=cidr_block, network=net, zone=zone)
  1137                                                   router = self.provider.networking.routers.get_or_create_default(net)
  1138                                                   router.attach_subnet(sn)
  1139                                                   gateway = net.gateways.get_or_create()
  1140                                                   router.attach_gateway(gateway)
  1141                                                   return sn

Total time: 8.01128 s
Function: label at line 1831

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1831                                               @label.setter
  1832                                               # pylint:disable=arguments-differ
  1833                                               @profile
  1834                                               def label(self, value):
  1835        23     110660.0   4811.3      1.4          req = (self._provider
  1836                                                              .gcp_compute
  1837                                                              .snapshots()
  1838        23        104.0      4.5      0.0                     .setLabels(project=self._provider.project_name,
  1839        23         55.0      2.4      0.0                                resource=self.name,
  1840        23      11267.0    489.9      0.1                                body={}))
  1841                                           
  1842        23    7889193.0 343008.4     98.5          helpers.change_label(self, 'cblabel', value, '_snapshot', req)

Total time: 6.71368 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         2          3.0      1.5      0.0          if not network:
   313         2          1.0      0.5      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         2          2.0      1.0      0.0          filters = ['label']
   317         2    6713590.0 3356795.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         2         87.0     43.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 5.81179 s
Function: get at line 1322

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1322                                               @dispatch(event="provider.storage.snapshots.get",
  1323                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1324                                               @profile
  1325                                               def get(self, snapshot_id):
  1326        23    5811432.0 252671.0    100.0          snapshot = self.provider.get_resource('snapshots', snapshot_id)
  1327        23        354.0     15.4      0.0          return GCPSnapshot(self.provider, snapshot) if snapshot else None

Total time: 5.71702 s
Function: label at line 1643

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1643                                               @label.setter
  1644                                               @profile
  1645                                               def label(self, value):
  1646        12      87830.0   7319.2      1.5          req = (self._provider
  1647                                                              .gcp_compute
  1648                                                              .disks()
  1649        12         29.0      2.4      0.0                     .setLabels(project=self._provider.project_name,
  1650        12       5123.0    426.9      0.1                                zone=self.zone_name,
  1651        12         39.0      3.2      0.0                                resource=self.name,
  1652        12       4668.0    389.0      0.1                                body={}))
  1653                                           
  1654        12    5619329.0 468277.4     98.3          helpers.change_label(self, 'cblabel', value, '_volume', req)

Total time: 5.41758 s
Function: delete at line 1303

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1303                                               @dispatch(event="provider.storage.volumes.delete",
  1304                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1305                                               @profile
  1306                                               def delete(self, volume):
  1307         7         11.0      1.6      0.0          volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
  1308         7          6.0      0.9      0.0          if volume:
  1309         7      56049.0   8007.0      1.0              (self._provider.gcp_compute
  1310                                                                      .disks()
  1311         7         29.0      4.1      0.0                             .delete(project=self.provider.project_name,
  1312         7       3047.0    435.3      0.1                                     zone=volume.zone_name,
  1313         7    5358442.0 765491.7     98.9                                     disk=volume.name)
  1314                                                                      .execute())

Total time: 4.29212 s
Function: refresh at line 1880

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1880                                               @profile
  1881                                               def refresh(self):
  1882                                                   """
  1883                                                   Refreshes the state of this snapshot by re-querying the cloud provider
  1884                                                   for its latest state.
  1885                                                   """
  1886        16    4292050.0 268253.1    100.0          snap = self._provider.storage.snapshots.get(self.id)
  1887        16         14.0      0.9      0.0          if snap:
  1888                                                       # pylint:disable=protected-access
  1889        16         53.0      3.3      0.0              self._snapshot = snap._snapshot
  1890                                                   else:
  1891                                                       # snapshot no longer exists
  1892                                                       self._snapshot['status'] = SnapshotState.UNKNOWN

Total time: 2.27445 s
Function: delete at line 1410

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1410                                               @dispatch(event="provider.storage.snapshots.delete",
  1411                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1412                                               @profile
  1413                                               def delete(self, snapshot):
  1414         3          7.0      2.3      0.0          snapshot = (snapshot if isinstance(snapshot, GCPSnapshot)
  1415                                                               else self.get(snapshot))
  1416         3          3.0      1.0      0.0          if snapshot:
  1417         3      15075.0   5025.0      0.7              (self.provider
  1418                                                            .gcp_compute
  1419                                                            .snapshots()
  1420         3         12.0      4.0      0.0                   .delete(project=self.provider.project_name,
  1421         3    2259355.0 753118.3     99.3                           snapshot=snapshot.name)
  1422                                                            .execute())

Total time: 1.73786 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         2          9.0      4.5      0.0          region = self.provider.get_resource('regions', region_id,
   387         2    1737809.0 868904.5    100.0                                              region=region_id)
   388         2         39.0     19.5      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 1.6972 s
Function: list at line 1360

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1360                                               @dispatch(event="provider.storage.snapshots.list",
  1361                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1362                                               @profile
  1363                                               def list(self, limit=None, marker=None):
  1364         9         17.0      1.9      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1365         9      48098.0   5344.2      2.8          response = (self.provider
  1366                                                                   .gcp_compute
  1367                                                                   .snapshots()
  1368         9         37.0      4.1      0.0                          .list(project=self.provider.project_name,
  1369         9          7.0      0.8      0.0                                maxResults=max_result,
  1370         9    1648652.0 183183.6     97.1                                pageToken=marker)
  1371                                                                   .execute())
  1372         9         30.0      3.3      0.0          snapshots = [GCPSnapshot(self.provider, snapshot)
  1373         9        237.0     26.3      0.0                       for snapshot in response.get('items', [])]
  1374         9         13.0      1.4      0.0          if len(snapshots) > max_result:
  1375                                                       log.warning('Expected at most %d results; got %d',
  1376                                                                   max_result, len(snapshots))
  1377         9         12.0      1.3      0.0          return ServerPagedResultList('nextPageToken' in response,
  1378         9         12.0      1.3      0.0                                       response.get('nextPageToken'),
  1379         9         87.0      9.7      0.0                                       False, data=snapshots)

Total time: 1.4284 s
Function: delete at line 704

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   704                                               @dispatch(event="provider.compute.instances.delete",
   705                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   706                                               @profile
   707                                               def delete(self, instance):
   708         2          4.0      2.0      0.0          instance = (instance if isinstance(instance, GCPInstance) else
   709                                                               self.get(instance))
   710         2          2.0      1.0      0.0          if instance:
   711         2      48134.0  24067.0      3.4              (self._provider
   712                                                        .gcp_compute
   713                                                        .instances()
   714         2          8.0      4.0      0.0               .delete(project=self.provider.project_name,
   715         2        947.0    473.5      0.1                       zone=instance.zone_name,
   716         2    1379301.0 689650.5     96.6                       instance=instance.name)
   717                                                        .execute())

Total time: 1.01982 s
Function: description at line 1851

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1851                                               @description.setter
  1852                                               @profile
  1853                                               def description(self, value):
  1854         1       3862.0   3862.0      0.4          req = (self._provider
  1855                                                          .gcp_compute
  1856                                                          .snapshots()
  1857         1          2.0      2.0      0.0                 .setLabels(project=self._provider.project_name,
  1858         1          2.0      2.0      0.0                            resource=self.name,
  1859         1        335.0    335.0      0.0                            body={}))
  1860                                           
  1861         1    1015623.0 1015623.0     99.6          helpers.change_label(self, 'description', value, '_snapshot', req)

Total time: 0.869076 s
Function: find at line 1329

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1329                                               @dispatch(event="provider.storage.snapshots.find",
  1330                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1331                                               @profile
  1332                                               def find(self, limit=None, marker=None, **kwargs):
  1333         6         12.0      2.0      0.0          label = kwargs.pop('label', None)
  1334                                           
  1335                                                   # All kwargs should have been popped at this time.
  1336         6         10.0      1.7      0.0          if len(kwargs) > 0:
  1337         2          2.0      1.0      0.0              raise InvalidParamException(
  1338         2          2.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1339         2         26.0     13.0      0.0                  "attributes: %s" % (kwargs, 'label'))
  1340                                           
  1341         4          5.0      1.2      0.0          filtr = 'labels.cblabel eq ' + label
  1342         4          5.0      1.2      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1343         4      19903.0   4975.8      2.3          response = (self.provider
  1344                                                                   .gcp_compute
  1345                                                                   .snapshots()
  1346         4         19.0      4.8      0.0                          .list(project=self.provider.project_name,
  1347         4          4.0      1.0      0.0                                filter=filtr,
  1348         4          1.0      0.2      0.0                                maxResults=max_result,
  1349         4     848956.0 212239.0     97.7                                pageToken=marker)
  1350                                                                   .execute())
  1351         4         15.0      3.8      0.0          snapshots = [GCPSnapshot(self.provider, snapshot)
  1352         4         60.0     15.0      0.0                       for snapshot in response.get('items', [])]
  1353         4          6.0      1.5      0.0          if len(snapshots) > max_result:
  1354                                                       log.warning('Expected at most %d results; got %d',
  1355                                                                   max_result, len(snapshots))
  1356         4          6.0      1.5      0.0          return ServerPagedResultList('nextPageToken' in response,
  1357         4          5.0      1.2      0.0                                       response.get('nextPageToken'),
  1358         4         39.0      9.8      0.0                                       False, data=snapshots)

Total time: 0.680887 s
Function: list at line 1238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1238                                               @dispatch(event="provider.storage.volumes.list",
  1239                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1240                                               @profile
  1241                                               def list(self, limit=None, marker=None):
  1242                                                   """
  1243                                                   List all volumes.
  1244                                           
  1245                                                   limit: The maximum number of volumes to return. The returned
  1246                                                          ResultList's is_truncated property can be used to determine
  1247                                                          whether more records are available.
  1248                                                   """
  1249                                                   # For GCP API, Acceptable values are 0 to 500, inclusive.
  1250                                                   # (Default: 500).
  1251         4          5.0      1.2      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1252         4      31965.0   7991.2      4.7          response = (self.provider
  1253                                                                   .gcp_compute
  1254                                                                   .disks()
  1255         4         16.0      4.0      0.0                          .list(project=self.provider.project_name,
  1256         4          4.0      1.0      0.0                                zone=self.provider.default_zone,
  1257         4          4.0      1.0      0.0                                maxResults=max_result,
  1258         4     648760.0 162190.0     95.3                                pageToken=marker)
  1259                                                                   .execute())
  1260         4         14.0      3.5      0.0          gcp_vols = [GCPVolume(self.provider, vol)
  1261         4         59.0     14.8      0.0                      for vol in response.get('items', [])]
  1262         4          7.0      1.8      0.0          if len(gcp_vols) > max_result:
  1263                                                       log.warning('Expected at most %d results; got %d',
  1264                                                                   max_result, len(gcp_vols))
  1265         4          5.0      1.2      0.0          return ServerPagedResultList('nextPageToken' in response,
  1266         4          5.0      1.2      0.0                                       response.get('nextPageToken'),
  1267         4         43.0     10.8      0.0                                       False, data=gcp_vols)

Total time: 0.512971 s
Function: list at line 1003

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1003                                               @dispatch(event="provider.networking.subnets.list",
  1004                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1005                                               @profile
  1006                                               def list(self, network=None, zone=None, limit=None, marker=None):
  1007                                                   """
  1008                                                   If the zone is not given, we list all subnets in the default region.
  1009                                                   """
  1010         2          2.0      1.0      0.0          filter = None
  1011         2          2.0      1.0      0.0          if network is not None:
  1012                                                       network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014                                                       filter = 'network eq %s' % network.resource_url
  1015         2          1.0      0.5      0.0          if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018         2          8.0      4.0      0.0              region_name = self.provider.region_name
  1019         2          0.0      0.0      0.0          subnets = []
  1020         2      28567.0  14283.5      5.6          response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023         2          9.0      4.5      0.0                          .list(project=self.provider.project_name,
  1024         2          2.0      1.0      0.0                                region=region_name,
  1025         2     484204.0 242102.0     94.4                                filter=filter)
  1026                                                                   .execute())
  1027        16         14.0      0.9      0.0          for subnet in response.get('items', []):
  1028        14         81.0      5.8      0.0              subnets.append(GCPSubnet(self.provider, subnet))
  1029         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider, subnets,
  1030         2         78.0     39.0      0.0                                       limit=limit, marker=marker)

Total time: 0.493297 s
Function: get at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @dispatch(event="provider.compute.vm_types.get",
   342                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   343                                               @profile
   344                                               def get(self, vm_type_id):
   345         2     493259.0 246629.5    100.0          vm_type = self.provider.get_resource('machineTypes', vm_type_id)
   346         2         38.0     19.0      0.0          return GCPVMType(self.provider, vm_type) if vm_type else None

Total time: 0.365001 s
Function: find at line 1203

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1203                                               @dispatch(event="provider.storage.volumes.find",
  1204                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1205                                               @profile
  1206                                               def find(self, limit=None, marker=None, **kwargs):
  1207                                                   """
  1208                                                   Searches for a volume by a given list of attributes.
  1209                                                   """
  1210         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
  1211                                           
  1212                                                   # All kwargs should have been popped at this time.
  1213         3          6.0      2.0      0.0          if len(kwargs) > 0:
  1214         1          2.0      2.0      0.0              raise InvalidParamException(
  1215         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1216         1         17.0     17.0      0.0                  "attributes: %s" % (kwargs, 'label'))
  1217                                           
  1218         2          3.0      1.5      0.0          filtr = 'labels.cblabel eq ' + label
  1219         2          2.0      1.0      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1220         2      16762.0   8381.0      4.6          response = (self.provider
  1221                                                                   .gcp_compute
  1222                                                                   .disks()
  1223         2          7.0      3.5      0.0                          .list(project=self.provider.project_name,
  1224         2          2.0      1.0      0.0                                zone=self.provider.default_zone,
  1225         2          2.0      1.0      0.0                                filter=filtr,
  1226         2          1.0      0.5      0.0                                maxResults=max_result,
  1227         2     348126.0 174063.0     95.4                                pageToken=marker)
  1228                                                                   .execute())
  1229         2          6.0      3.0      0.0          gcp_vols = [GCPVolume(self.provider, vol)
  1230         2         24.0     12.0      0.0                      for vol in response.get('items', [])]
  1231         2          4.0      2.0      0.0          if len(gcp_vols) > max_result:
  1232                                                       log.warning('Expected at most %d results; got %d',
  1233                                                                   max_result, len(gcp_vols))
  1234         2          3.0      1.5      0.0          return ServerPagedResultList('nextPageToken' in response,
  1235         2          4.0      2.0      0.0                                       response.get('nextPageToken'),
  1236         2         23.0     11.5      0.0                                       False, data=gcp_vols)

Total time: 0.350549 s
Function: get at line 435

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   435                                               @profile
   436                                               def get(self, image_id):
   437                                                   """
   438                                                   Returns an Image given its id
   439                                                   """
   440         2     350509.0 175254.5    100.0          image = self.provider.get_resource('images', image_id)
   441         2          5.0      2.5      0.0          if image:
   442         2         35.0     17.5      0.0              return GCPMachineImage(self.provider, image)
   443                                                   self._retrieve_public_images()
   444                                                   for public_image in self._public_images:
   445                                                       if public_image.id == image_id or public_image.name == image_id:
   446                                                           return public_image
   447                                                   return None

