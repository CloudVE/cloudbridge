cloudbridge.test.test_compute_service.CloudComputeServiceTestCase


Error during cleanup: CloudBridgeBaseException: <HttpError 404 when requesting https://www.googleapis.com/compute/v1/projects/cloudbridge-dev/zones/us-central1-a/disks/cb-blkattch-b77ddf-aafd60?alt=json returned "The resource 'projects/cloudbridge-dev/zones/us-central1-a/disks/cb-blkattch-b77ddf-aafd60' was not found"> from exception type: <class 'googleapiclient.errors.HttpError'>
Error during cleanup: 'NoneType' object has no attribute '_ip'
Test output
 ......
----------------------------------------------------------------------
Ran 6 tests in 1529.464s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 245.431 s
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
   653       725  245415590.0 338504.3    100.0          instance = self.provider.get_resource('instances', instance_id)
   654       725      14964.0     20.6      0.0          return GCPInstance(self.provider, instance) if instance else None

Total time: 242.841 s
Function: refresh at line 1237

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1237                                               @profile
  1238                                               def refresh(self):
  1239                                                   """
  1240                                                   Refreshes the state of this instance by re-querying the cloud provider
  1241                                                   for its latest state.
  1242                                                   """
  1243       716  242833071.0 339152.3    100.0          inst = self._provider.compute.instances.get(self.id)
  1244       716        819.0      1.1      0.0          if inst:
  1245                                                       # pylint:disable=protected-access
  1246       711       6944.0      9.8      0.0              self._gcp_instance = inst._gcp_instance
  1247                                                   else:
  1248                                                       # instance no longer exists
  1249         5         18.0      3.6      0.0              self._gcp_instance['status'] = InstanceState.UNKNOWN

Total time: 241.941 s
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
   499        14        184.0     13.1      0.0          GCPInstance.assert_valid_resource_name(label)
   500         4         22.0      5.5      0.0          zone_name = self.provider.default_zone
   501         4          8.0      2.0      0.0          if zone:
   502         4         14.0      3.5      0.0              if not isinstance(zone, GCPPlacementZone):
   503         4          7.0      1.8      0.0                  zone = GCPPlacementZone(
   504         4         11.0      2.8      0.0                      self.provider,
   505         4     635237.0 158809.2      0.3                      self.provider.get_resource('zones', zone))
   506         4         26.0      6.5      0.0              zone_name = zone.name
   507         4         20.0      5.0      0.0          if not isinstance(vm_type, GCPVMType):
   508         4     676873.0 169218.2      0.3              vm_type = self.provider.compute.vm_types.get(vm_type)
   509                                           
   510         4         12.0      3.0      0.0          network_interface = {'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
   511         4         14.0      3.5      0.0                                                  'name': 'External NAT'}]}
   512         4         13.0      3.2      0.0          if subnet:
   513         4         29.0      7.2      0.0              network_interface['subnetwork'] = subnet.id
   514                                                   else:
   515                                                       network_interface['network'] = 'global/networks/default'
   516                                           
   517         4         11.0      2.8      0.0          num_roots = 0
   518         4          9.0      2.2      0.0          disks = []
   519         4         11.0      2.8      0.0          boot_disk = None
   520         4         14.0      3.5      0.0          if isinstance(launch_config, GCPLaunchConfig):
   521        17         52.0      3.1      0.0              for disk in launch_config.block_devices:
   522        16         48.0      3.0      0.0                  if not disk.source:
   523        13        810.0     62.3      0.0                      volume_name = 'disk-{0}'.format(uuid.uuid4())
   524        13         43.0      3.3      0.0                      volume_size = disk.size if disk.size else 1
   525        13        184.0     14.2      0.0                      volume = self.provider.storage.volumes.create(
   526        13   17742244.0 1364788.0      7.3                          volume_name, volume_size, zone)
   527        13   16957937.0 1304456.7      7.0                      volume.wait_till_ready()
   528        13         38.0      2.9      0.0                      source_field = 'source'
   529        13         59.0      4.5      0.0                      source_value = volume.id
   530         3         14.0      4.7      0.0                  elif isinstance(disk.source, GCPMachineImage):
   531         1          2.0      2.0      0.0                      source_field = 'initializeParams'
   532                                                               # Explicitly set diskName; otherwise, instance label will
   533                                                               # be used by default which may collide with existing disks.
   534                                                               source_value = {
   535         1          7.0      7.0      0.0                          'sourceImage': disk.source.id,
   536         1         70.0     70.0      0.0                          'diskName': 'image-disk-{0}'.format(uuid.uuid4()),
   537         1          5.0      5.0      0.0                          'diskSizeGb': disk.size if disk.size else 20}
   538         2          7.0      3.5      0.0                  elif isinstance(disk.source, GCPVolume):
   539         1          2.0      2.0      0.0                      source_field = 'source'
   540         1          5.0      5.0      0.0                      source_value = disk.source.id
   541         1          4.0      4.0      0.0                  elif isinstance(disk.source, GCPSnapshot):
   542         1    1637892.0 1637892.0      0.7                      volume = disk.source.create_volume(zone, size=disk.size)
   543         1   20995545.0 20995545.0      8.7                      volume.wait_till_ready()
   544         1          3.0      3.0      0.0                      source_field = 'source'
   545         1          5.0      5.0      0.0                      source_value = volume.id
   546                                                           else:
   547                                                               log.warning('Unknown disk source')
   548                                                               continue
   549        16         45.0      2.8      0.0                  autoDelete = True
   550        16         53.0      3.3      0.0                  if disk.delete_on_terminate is not None:
   551         4         12.0      3.0      0.0                      autoDelete = disk.delete_on_terminate
   552        16         57.0      3.6      0.0                  num_roots += 1 if disk.is_root else 0
   553        16         45.0      2.8      0.0                  if disk.is_root and not boot_disk:
   554         1          3.0      3.0      0.0                      boot_disk = {'boot': True,
   555         1          3.0      3.0      0.0                                   'autoDelete': autoDelete,
   556         1          3.0      3.0      0.0                                   source_field: source_value}
   557                                                           else:
   558        15         47.0      3.1      0.0                      disks.append({'boot': False,
   559        15         39.0      2.6      0.0                                    'autoDelete': autoDelete,
   560        15         56.0      3.7      0.0                                    source_field: source_value})
   561                                           
   562         4         11.0      2.8      0.0          if num_roots > 1:
   563                                                       log.warning('The launch config contains %d boot disks. Will '
   564                                                                   'use the first one', num_roots)
   565         4         11.0      2.8      0.0          if image:
   566         4         10.0      2.5      0.0              if boot_disk:
   567         1        229.0    229.0      0.0                  log.warning('A boot image is given while the launch config '
   568                                                                       'contains a boot disk, too. The launch config '
   569                                                                       'will be used.')
   570                                                       else:
   571         3         10.0      3.3      0.0                  if not isinstance(image, GCPMachineImage):
   572         3     553853.0 184617.7      0.2                      image = self.provider.compute.images.get(image)
   573                                                           # Explicitly set diskName; otherwise, instance name will be
   574                                                           # used by default which may conflict with existing disks.
   575                                                           boot_disk = {
   576         3          8.0      2.7      0.0                      'boot': True,
   577         3          8.0      2.7      0.0                      'autoDelete': True,
   578                                                               'initializeParams': {
   579         3         17.0      5.7      0.0                          'sourceImage': image.id,
   580         3        189.0     63.0      0.0                          'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}
   581                                           
   582         4         13.0      3.2      0.0          if not boot_disk:
   583                                                       log.warning('No boot disk is given for instance %s.', label)
   584                                                       return None
   585                                                   # The boot disk must be the first disk attached to the instance.
   586         4         17.0      4.2      0.0          disks.insert(0, boot_disk)
   587                                           
   588                                                   config = {
   589         4        230.0     57.5      0.0              'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
   590         4         32.0      8.0      0.0              'machineType': vm_type.resource_url,
   591         4         11.0      2.8      0.0              'disks': disks,
   592         4         15.0      3.8      0.0              'networkInterfaces': [network_interface]
   593                                                   }
   594                                           
   595         4         12.0      3.0      0.0          if vm_firewalls and isinstance(vm_firewalls, list):
   596         1          3.0      3.0      0.0              vm_firewall_names = []
   597         1          4.0      4.0      0.0              if isinstance(vm_firewalls[0], VMFirewall):
   598         1         10.0     10.0      0.0                  vm_firewall_names = [f.name for f in vm_firewalls]
   599                                                       elif isinstance(vm_firewalls[0], str):
   600                                                           vm_firewall_names = vm_firewalls
   601         1          3.0      3.0      0.0              if len(vm_firewall_names) > 0:
   602         1          4.0      4.0      0.0                  config['tags'] = {}
   603         1          4.0      4.0      0.0                  config['tags']['items'] = vm_firewall_names
   604                                           
   605         4         11.0      2.8      0.0          if user_data:
   606                                                       entry = {'key': 'user-data', 'value': user_data}
   607                                                       config['metadata'] = {'items': [entry]}
   608                                           
   609         4         11.0      2.8      0.0          if key_pair:
   610         1          3.0      3.0      0.0              if not isinstance(key_pair, GCPKeyPair):
   611                                                           key_pair = self._provider.security.key_pairs.get(key_pair)
   612         1          3.0      3.0      0.0              if key_pair:
   613         1          3.0      3.0      0.0                  kp = key_pair._key_pair
   614                                                           kp_entry = {
   615         1          3.0      3.0      0.0                      "key": "ssh-keys",
   616                                                               # Format is not removed from public key portion
   617         1          3.0      3.0      0.0                      "value": "{}:{} {}".format(
   618         1         10.0     10.0      0.0                          self.provider.vm_default_user_name,
   619         1          5.0      5.0      0.0                          kp.public_key,
   620         1          7.0      7.0      0.0                          kp.name)
   621                                                               }
   622         1          4.0      4.0      0.0                  meta = config.get('metadata', {})
   623         1          3.0      3.0      0.0                  if meta:
   624                                                               items = meta.get('items', [])
   625                                                               items.append(kp_entry)
   626                                                           else:
   627         1          4.0      4.0      0.0                      config['metadata'] = {'items': [kp_entry]}
   628                                           
   629         4         13.0      3.2      0.0          config['labels'] = {'cblabel': label}
   630                                           
   631         4     108434.0  27108.5      0.0          operation = (self.provider
   632                                                                    .gcp_compute.instances()
   633         4         31.0      7.8      0.0                           .insert(project=self.provider.project_name,
   634         4          7.0      1.8      0.0                                   zone=zone_name,
   635         4    5754771.0 1438692.8      2.4                                   body=config)
   636                                                                    .execute())
   637         4         17.0      4.2      0.0          instance_id = operation.get('targetLink')
   638         4  175462029.0 43865507.2     72.5          self.provider.wait_for_operation(operation, zone=zone_name)
   639         4    1412949.0 353237.2      0.6          cb_inst = self.get(instance_id)
   640         4         13.0      3.2      0.0          return cb_inst

Total time: 36.3814 s
Function: create at line 205

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   205                                               @dispatch(event="provider.security.vm_firewalls.create",
   206                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   207                                               @profile
   208                                               def create(self, label, network, description=None):
   209         2         22.0     11.0      0.0          GCPVMFirewall.assert_valid_resource_label(label)
   210         2          5.0      2.5      0.0          network = (network if isinstance(network, GCPNetwork)
   211         2     510381.0 255190.5      1.4                     else self.provider.networking.networks.get(network))
   212         2         46.0     23.0      0.0          fw = GCPVMFirewall(self._delegate, label, network, description)
   213         2   19958778.0 9979389.0     54.9          fw.label = label
   214                                                   # This rule exists implicitly. Add it explicitly so that the firewall
   215                                                   # is not empty and the rule is shown by list/get/find methods.
   216                                                   # pylint:disable=protected-access
   217         2         26.0     13.0      0.0          self.provider.security._vm_firewall_rules.create_with_priority(
   218         2         10.0      5.0      0.0              fw, direction=TrafficDirection.OUTBOUND, protocol='tcp',
   219         2   15912115.0 7956057.5     43.7              priority=65534, cidr='0.0.0.0/0')
   220         2          1.0      0.5      0.0          return fw

Total time: 28.846 s
Function: delete at line 222

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   222                                               @dispatch(event="provider.security.vm_firewalls.delete",
   223                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   224                                               @profile
   225                                               def delete(self, vm_firewall):
   226         2         57.0     28.5      0.0          fw_id = (vm_firewall.id if isinstance(vm_firewall, GCPVMFirewall)
   227                                                            else vm_firewall)
   228         2   28845964.0 14422982.0    100.0          return self._delegate.delete_tag_network_with_id(fw_id)

Total time: 25.7981 s
Function: create at line 1032

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1032                                               @dispatch(event="provider.networking.subnets.create",
  1033                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1034                                               @profile
  1035                                               def create(self, label, network, cidr_block, zone):
  1036                                                   """
  1037                                                   GCP subnets are regional. The region is inferred from the zone;
  1038                                                   otherwise, the default region, as set in the
  1039                                                   provider, is used.
  1040                                           
  1041                                                   If a subnet with overlapping IP range exists already, we return that
  1042                                                   instead of creating a new subnet. In this case, other parameters, i.e.
  1043                                                   the name and the zone, are ignored.
  1044                                                   """
  1045         1         11.0     11.0      0.0          GCPSubnet.assert_valid_resource_label(label)
  1046         1         52.0     52.0      0.0          name = GCPSubnet._generate_name_from_label(label, 'cbsubnet')
  1047         1          9.0      9.0      0.0          region_name = self._zone_to_region(zone)
  1048                                           #         for subnet in self.iter(network=network):
  1049                                           #            if BaseNetwork.cidr_blocks_overlap(subnet.cidr_block, cidr_block):
  1050                                           #                 if subnet.region_name != region_name:
  1051                                           #                     log.error('Failed to create subnetwork in region %s: '
  1052                                           #                                  'the given IP range %s overlaps with a '
  1053                                           #                                  'subnetwork in a different region %s',
  1054                                           #                                  region_name, cidr_block, subnet.region_name)
  1055                                           #                     return None
  1056                                           #                 return subnet
  1057                                           #             if subnet.label == label and subnet.region_name == region_name:
  1058                                           #                 return subnet
  1059                                           
  1060         1          1.0      1.0      0.0          body = {'ipCidrRange': cidr_block,
  1061         1          1.0      1.0      0.0                  'name': name,
  1062         1          3.0      3.0      0.0                  'network': network.resource_url,
  1063         1          1.0      1.0      0.0                  'region': region_name
  1064                                                           }
  1065         1      11972.0  11972.0      0.0          response = (self.provider
  1066                                                                   .gcp_compute
  1067                                                                   .subnetworks()
  1068         1          4.0      4.0      0.0                          .insert(project=self.provider.project_name,
  1069         1          0.0      0.0      0.0                                  region=region_name,
  1070         1    1025636.0 1025636.0      4.0                                  body=body)
  1071                                                                   .execute())
  1072         1   16362161.0 16362161.0     63.4          self.provider.wait_for_operation(response, region=region_name)
  1073         1     351602.0 351602.0      1.4          cb_subnet = self.get(name)
  1074         1    8046680.0 8046680.0     31.2          cb_subnet.label = label
  1075         1          2.0      2.0      0.0          return cb_subnet

Total time: 25.4765 s
Function: delete at line 861

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   861                                               @dispatch(event="provider.networking.networks.delete",
   862                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   863                                               @profile
   864                                               def delete(self, network):
   865                                                   # Accepts network object
   866         1          2.0      2.0      0.0          if isinstance(network, GCPNetwork):
   867         1          3.0      3.0      0.0              name = network.name
   868                                                   # Accepts both name and ID
   869                                                   elif 'googleapis' in network:
   870                                                       name = network.split('/')[-1]
   871                                                   else:
   872                                                       name = network
   873         1       5053.0   5053.0      0.0          response = (self.provider
   874                                                                   .gcp_compute
   875                                                                   .networks()
   876         1          3.0      3.0      0.0                          .delete(project=self.provider.project_name,
   877         1     967890.0 967890.0      3.8                                  network=name)
   878                                                                   .execute())
   879         1   16367108.0 16367108.0     64.2          self.provider.wait_for_operation(response)
   880                                                   # Remove label
   881         1          4.0      4.0      0.0          tag_name = "_".join(["network", name, "label"])
   882         1    8136406.0 8136406.0     31.9          if not helpers.remove_metadata_item(self.provider, tag_name):
   883                                                       log.warning('No label was found associated with this network '
   884                                                                   '"{}" when deleted.'.format(network))
   885         1          2.0      2.0      0.0          return True

Total time: 22.9287 s
Function: create at line 824

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   824                                               @dispatch(event="provider.networking.networks.create",
   825                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   826                                               @profile
   827                                               def create(self, label, cidr_block):
   828                                                   """
   829                                                   Creates an auto mode VPC network with default subnets. It is possible
   830                                                   to add additional subnets later.
   831                                                   """
   832         1          9.0      9.0      0.0          GCPNetwork.assert_valid_resource_label(label)
   833         1         41.0     41.0      0.0          name = GCPNetwork._generate_name_from_label(label, 'cbnet')
   834         1          1.0      1.0      0.0          body = {'name': name}
   835                                                   # This results in a custom mode network
   836         1          0.0      0.0      0.0          body['autoCreateSubnetworks'] = False
   837         1     193516.0 193516.0      0.8          response = (self.provider
   838                                                                   .gcp_compute
   839                                                                   .networks()
   840         1          4.0      4.0      0.0                          .insert(project=self.provider.project_name,
   841         1    1227328.0 1227328.0      5.4                                  body=body)
   842                                                                   .execute())
   843         1   13926261.0 13926261.0     60.7          self.provider.wait_for_operation(response)
   844         1     264097.0 264097.0      1.2          cb_net = self.get(name)
   845         1    7317483.0 7317483.0     31.9          cb_net.label = label
   846         1          1.0      1.0      0.0          return cb_net

Total time: 22.513 s
Function: delete at line 1077

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1077                                               @dispatch(event="provider.networking.subnets.delete",
  1078                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1079                                               @profile
  1080                                               def delete(self, subnet):
  1081         1          3.0      3.0      0.0          sn = subnet if isinstance(subnet, GCPSubnet) else self.get(subnet)
  1082         1          1.0      1.0      0.0          if not sn:
  1083                                                       return
  1084         1       9758.0   9758.0      0.0          response = (self.provider
  1085                                                               .gcp_compute
  1086                                                               .subnetworks()
  1087         1          5.0      5.0      0.0                      .delete(project=self.provider.project_name,
  1088         1        371.0    371.0      0.0                              region=sn.region_name,
  1089         1     819133.0 819133.0      3.6                              subnetwork=sn.name)
  1090                                                               .execute())
  1091         1   14504569.0 14504569.0     64.4          self.provider.wait_for_operation(response, region=sn.region_name)
  1092                                                   # Remove label
  1093         1         11.0     11.0      0.0          tag_name = "_".join(["subnet", sn.name, "label"])
  1094         1    7179153.0 7179153.0     31.9          if not helpers.remove_metadata_item(self._provider, tag_name):
  1095                                                       log.warning('No label was found associated with this subnet '
  1096                                                                   '"{}" when deleted.'.format(sn.name))

Total time: 19.9587 s
Function: label at line 482

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   482                                               @label.setter
   483                                               @profile
   484                                               def label(self, value):
   485         2         17.0      8.5      0.0          self.assert_valid_resource_label(value)
   486         2          8.0      4.0      0.0          tag_name = "_".join(["firewall", self.name, "label"])
   487         2   19958719.0 9979359.5    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 19.7516 s
Function: create at line 1269

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1269                                               @dispatch(event="provider.storage.volumes.create",
  1270                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1271                                               @profile
  1272                                               def create(self, label, size, zone, snapshot=None, description=None):
  1273        14        150.0     10.7      0.0          GCPVolume.assert_valid_resource_label(label)
  1274        14        678.0     48.4      0.0          name = GCPVolume._generate_name_from_label(label, 'cb-vol')
  1275        14         27.0      1.9      0.0          if not isinstance(zone, GCPPlacementZone):
  1276         1          1.0      1.0      0.0              zone = GCPPlacementZone(
  1277         1          1.0      1.0      0.0                  self.provider,
  1278         1     826571.0 826571.0      4.2                  self.provider.get_resource('zones', zone))
  1279        14         55.0      3.9      0.0          zone_name = zone.name
  1280        14         16.0      1.1      0.0          snapshot_id = snapshot.id if isinstance(
  1281        14         32.0      2.3      0.0              snapshot, GCPSnapshot) and snapshot else snapshot
  1282        14         19.0      1.4      0.0          labels = {'cblabel': label}
  1283        14         19.0      1.4      0.0          if description:
  1284                                                       labels['description'] = description
  1285                                                   disk_body = {
  1286        14         13.0      0.9      0.0              'name': name,
  1287        14         16.0      1.1      0.0              'sizeGb': size,
  1288        14         48.0      3.4      0.0              'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
  1289        14         16.0      1.1      0.0              'sourceSnapshot': snapshot_id,
  1290        14         22.0      1.6      0.0              'labels': labels
  1291                                                   }
  1292        14     129817.0   9272.6      0.7          operation = (self.provider
  1293                                                                    .gcp_compute
  1294                                                                    .disks()
  1295                                                                    .insert(
  1296        14         35.0      2.5      0.0                               project=self._provider.project_name,
  1297        14         13.0      0.9      0.0                               zone=zone_name,
  1298        14   13700287.0 978591.9     69.4                               body=disk_body)
  1299                                                                    .execute())
  1300        14    5093711.0 363836.5     25.8          cb_vol = self.get(operation.get('targetLink'))
  1301        14         18.0      1.3      0.0          return cb_vol

Total time: 18.3208 s
Function: list at line 1645

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1645                                               @dispatch(event="provider.networking.floating_ips.list",
  1646                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1647                                               @profile
  1648                                               def list(self, gateway, limit=None, marker=None):
  1649        13         24.0      1.8      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1650        13      53702.0   4130.9      0.3          response = (self.provider
  1651                                                                   .gcp_compute
  1652                                                                   .addresses()
  1653        13         50.0      3.8      0.0                          .list(project=self.provider.project_name,
  1654        13         18.0      1.4      0.0                                region=self.provider.region_name,
  1655        13         12.0      0.9      0.0                                maxResults=max_result,
  1656        13    5317579.0 409044.5     29.0                                pageToken=marker)
  1657                                                                   .execute())
  1658        13         47.0      3.6      0.0          ips = [GCPFloatingIP(self.provider, ip)
  1659        13   12949130.0 996086.9     70.7                 for ip in response.get('items', [])]
  1660        13         42.0      3.2      0.0          if len(ips) > max_result:
  1661                                                       log.warning('Expected at most %d results; got %d',
  1662                                                                   max_result, len(ips))
  1663        13         21.0      1.6      0.0          return ServerPagedResultList('nextPageToken' in response,
  1664        13         25.0      1.9      0.0                                       response.get('nextPageToken'),
  1665        13        148.0     11.4      0.0                                       False, data=ips)

Total time: 15.9121 s
Function: create_with_priority at line 284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   284                                               @profile
   285                                               def create_with_priority(self, firewall, direction, protocol, priority,
   286                                                                        from_port=None, to_port=None, cidr=None,
   287                                                                        src_dest_fw=None):
   288         2          8.0      4.0      0.0          port = GCPVMFirewallRuleService.to_port_range(from_port, to_port)
   289         2          2.0      1.0      0.0          src_dest_tag = None
   290         2          1.0      0.5      0.0          src_dest_fw_id = None
   291         2          2.0      1.0      0.0          if src_dest_fw:
   292                                                       src_dest_tag = src_dest_fw.name
   293                                                       src_dest_fw_id = src_dest_fw.id
   294         2          9.0      4.5      0.0          if not firewall.delegate.add_firewall(
   295         2          5.0      2.5      0.0                  firewall.name, direction, protocol, priority, port, cidr,
   296         2          7.0      3.5      0.0                  src_dest_tag, firewall.description,
   297         2   15863023.0 7931511.5     99.7                  firewall.network.name):
   298                                                       return None
   299         2          7.0      3.5      0.0          rules = self.find(firewall, direction=direction, protocol=protocol,
   300         2          1.0      0.5      0.0                            from_port=from_port, to_port=to_port, cidr=cidr,
   301         2      48992.0  24496.0      0.3                            src_dest_fw_id=src_dest_fw_id)
   302         2          2.0      1.0      0.0          if len(rules) < 1:
   303         2          1.0      0.5      0.0              return None
   304                                                   return rules[0]

Total time: 14.5569 s
Function: get at line 1196

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1196                                               @dispatch(event="provider.storage.volumes.get",
  1197                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1198                                               @profile
  1199                                               def get(self, volume_id):
  1200        45   14556025.0 323467.2    100.0          vol = self.provider.get_resource('disks', volume_id)
  1201        45        900.0     20.0      0.0          return GCPVolume(self.provider, vol) if vol else None

Total time: 13.8162 s
Function: label at line 822

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   822                                               @label.setter
   823                                               # pylint:disable=arguments-differ
   824                                               @profile
   825                                               def label(self, value):
   826        11     219616.0  19965.1      1.6          req = (self._provider
   827                                                              .gcp_compute
   828                                                              .instances()
   829        11         39.0      3.5      0.0                     .setLabels(project=self._provider.project_name,
   830        11       4303.0    391.2      0.0                                zone=self.zone_name,
   831        11         24.0      2.2      0.0                                instance=self.name,
   832        11       4395.0    399.5      0.0                                body={}))
   833                                           
   834        11   13587832.0 1235257.5     98.3          helpers.change_label(self, 'cblabel', value, '_gcp_instance', req)

Total time: 13.7372 s
Function: create at line 935

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   935                                               @dispatch(event="provider.networking.routers.create",
   936                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   937                                               @profile
   938                                               def create(self, label, network):
   939         1          3.0      3.0      0.0          log.debug("Creating GCP Router Service with params "
   940         1         10.0     10.0      0.0                    "[label: %s network: %s]", label, network)
   941         1         13.0     13.0      0.0          GCPRouter.assert_valid_resource_label(label)
   942         1         53.0     53.0      0.0          name = GCPRouter._generate_name_from_label(label, 'cb-router')
   943                                           
   944         1          1.0      1.0      0.0          if not isinstance(network, GCPNetwork):
   945                                                       network = self.provider.networking.networks.get(network)
   946         1          4.0      4.0      0.0          network_url = network.resource_url
   947         1          4.0      4.0      0.0          region_name = self.provider.region_name
   948         1      11796.0  11796.0      0.1          response = (self.provider
   949                                                                   .gcp_compute
   950                                                                   .routers()
   951         1          3.0      3.0      0.0                          .insert(project=self.provider.project_name,
   952         1          1.0      1.0      0.0                                  region=region_name,
   953         1          0.0      0.0      0.0                                  body={'name': name,
   954         1    1130879.0 1130879.0      8.2                                        'network': network_url})
   955                                                                   .execute())
   956         1    1968172.0 1968172.0     14.3          self.provider.wait_for_operation(response, region=region_name)
   957         1     409329.0 409329.0      3.0          cb_router = self.get(name)
   958         1   10216949.0 10216949.0     74.4          cb_router.label = label
   959         1          2.0      2.0      0.0          return cb_router

Total time: 13.1326 s
Function: create at line 1381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1381                                               @dispatch(event="provider.storage.snapshots.create",
  1382                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1383                                               @profile
  1384                                               def create(self, label, volume, description=None):
  1385         1         10.0     10.0      0.0          GCPSnapshot.assert_valid_resource_label(label)
  1386         1         53.0     53.0      0.0          name = GCPSnapshot._generate_name_from_label(label, 'cbsnap')
  1387         1          4.0      4.0      0.0          volume_name = volume.name if isinstance(volume, GCPVolume) else volume
  1388         1          1.0      1.0      0.0          labels = {'cblabel': label}
  1389         1          1.0      1.0      0.0          if description:
  1390         1          1.0      1.0      0.0              labels['description'] = description
  1391                                                   snapshot_body = {
  1392         1          1.0      1.0      0.0              "name": name,
  1393         1          1.0      1.0      0.0              "labels": labels
  1394                                                   }
  1395         1       8395.0   8395.0      0.1          operation = (self.provider
  1396                                                                    .gcp_compute
  1397                                                                    .disks()
  1398                                                                    .createSnapshot(
  1399         1          3.0      3.0      0.0                               project=self.provider.project_name,
  1400         1          1.0      1.0      0.0                               zone=self.provider.default_zone,
  1401         1     876631.0 876631.0      6.7                               disk=volume_name, body=snapshot_body)
  1402                                                                    .execute())
  1403         1          2.0      2.0      0.0          if 'zone' not in operation:
  1404                                                       return None
  1405         1          8.0      8.0      0.0          self.provider.wait_for_operation(operation,
  1406         1   11986182.0 11986182.0     91.3                                           zone=self.provider.default_zone)
  1407         1     261346.0 261346.0      2.0          cb_snap = self.get(name)
  1408         1          1.0      1.0      0.0          return cb_snap

Total time: 10.9667 s
Function: delete at line 961

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   961                                               @dispatch(event="provider.networking.routers.delete",
   962                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   963                                               @profile
   964                                               def delete(self, router):
   965         1          3.0      3.0      0.0          r = router if isinstance(router, GCPRouter) else self.get(router)
   966         1          1.0      1.0      0.0          if r:
   967         1       7093.0   7093.0      0.1              (self.provider
   968                                                        .gcp_compute
   969                                                        .routers()
   970         1          3.0      3.0      0.0               .delete(project=self.provider.project_name,
   971         1        318.0    318.0      0.0                       region=r.region_name,
   972         1     611062.0 611062.0      5.6                       router=r.name)
   973                                                        .execute())
   974                                                       # Remove label
   975         1          8.0      8.0      0.0              tag_name = "_".join(["router", r.name, "label"])
   976         1   10348188.0 10348188.0     94.4              if not helpers.remove_metadata_item(self.provider, tag_name):
   977                                                           log.warning('No label was found associated with this router '
   978                                                                       '"{}" when deleted.'.format(r.name))

Total time: 10.2169 s
Function: label at line 1445

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1445                                               @label.setter
  1446                                               @profile
  1447                                               def label(self, value):
  1448         1          6.0      6.0      0.0          self.assert_valid_resource_label(value)
  1449         1          3.0      3.0      0.0          tag_name = "_".join(["router", self.name, "label"])
  1450         1   10216885.0 10216885.0    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 9.36634 s
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
  1108         3          7.0      2.3      0.0          region = self._zone_to_region(zone or self.provider.default_zone,
  1109         3    1330108.0 443369.3     14.2                                        return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111         3    8036183.0 2678727.7     85.8          for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112         3         33.0     11.0      0.0              if sn.region == region.id:
  1113         3          9.0      3.0      0.0                  return sn
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

Total time: 9.10339 s
Function: refresh at line 1789

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1789                                               @profile
  1790                                               def refresh(self):
  1791                                                   """
  1792                                                   Refreshes the state of this volume by re-querying the cloud provider
  1793                                                   for its latest state.
  1794                                                   """
  1795        30    9103248.0 303441.6    100.0          vol = self._provider.storage.volumes.get(self.id)
  1796        30         36.0      1.2      0.0          if vol:
  1797                                                       # pylint:disable=protected-access
  1798        30        111.0      3.7      0.0              self._volume = vol._volume
  1799                                                   else:
  1800                                                       # volume no longer exists
  1801                                                       self._volume['status'] = VolumeState.UNKNOWN

Total time: 8.04666 s
Function: label at line 1565

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1565                                               @label.setter
  1566                                               @profile
  1567                                               def label(self, value):
  1568         1          8.0      8.0      0.0          self.assert_valid_resource_label(value)
  1569         1          4.0      4.0      0.0          tag_name = "_".join(["subnet", self.name, "label"])
  1570         1    8046653.0 8046653.0    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 7.99967 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         3          3.0      1.0      0.0          if not network:
   313         3          1.0      0.3      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         3          3.0      1.0      0.0          filters = ['label']
   317         3    7999509.0 2666503.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         3        158.0     52.7      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 7.70415 s
Function: delete at line 164

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   164                                               @dispatch(event="provider.security.key_pairs.delete",
   165                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   166                                               @profile
   167                                               def delete(self, key_pair):
   168         1          3.0      3.0      0.0          key_pair = (key_pair if isinstance(key_pair, GCPKeyPair) else
   169         1     241435.0 241435.0      3.1                      self.get(key_pair))
   170         1          0.0      0.0      0.0          if key_pair:
   171         1          1.0      1.0      0.0              helpers.remove_metadata_item(
   172         1    7462710.0 7462710.0     96.9                  self.provider, GCPKeyPair.KP_TAG_PREFIX + key_pair.name)

Total time: 7.31747 s
Function: label at line 1305

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1305                                               @label.setter
  1306                                               @profile
  1307                                               def label(self, value):
  1308         1          8.0      8.0      0.0          self.assert_valid_resource_label(value)
  1309         1          4.0      4.0      0.0          tag_name = "_".join(["network", self.name, "label"])
  1310         1    7317456.0 7317456.0    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 5.62269 s
Function: create at line 137

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   137                                               @dispatch(event="provider.security.key_pairs.create",
   138                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   139                                               @profile
   140                                               def create(self, name, public_key_material=None):
   141         1          9.0      9.0      0.0          GCPKeyPair.assert_valid_resource_name(name)
   142         1          1.0      1.0      0.0          private_key = None
   143         1          1.0      1.0      0.0          if not public_key_material:
   144         1     150514.0 150514.0      2.7              public_key_material, private_key = cb_helpers.generate_key_pair()
   145                                                   # TODO: Add support for other formats not assume ssh-rsa
   146                                                   elif "ssh-rsa" not in public_key_material:
   147                                                       public_key_material = "ssh-rsa {}".format(public_key_material)
   148         1          5.0      5.0      0.0          kp_info = GCPKeyPair.GCPKeyInfo(name, public_key_material)
   149         1         39.0     39.0      0.0          metadata_value = json.dumps(kp_info._asdict())
   150         1          1.0      1.0      0.0          try:
   151         1          5.0      5.0      0.0              helpers.add_metadata_item(self.provider,
   152         1          1.0      1.0      0.0                                        GCPKeyPair.KP_TAG_PREFIX + name,
   153         1    5472093.0 5472093.0     97.3                                        metadata_value)
   154         1         19.0     19.0      0.0              return GCPKeyPair(self.provider, kp_info, private_key)
   155                                                   except googleapiclient.errors.HttpError as err:
   156                                                       if err.resp.get('content-type', '').startswith('application/json'):
   157                                                           message = (json.loads(err.content).get('error', {})
   158                                                                      .get('errors', [{}])[0].get('message'))
   159                                                           if "duplicate keys" in message:
   160                                                               raise DuplicateResourceException(
   161                                                                   'A KeyPair with name {0} already exists'.format(name))
   162                                                       raise

Total time: 4.11383 s
Function: delete at line 1683

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1683                                               @dispatch(event="provider.networking.floating_ips.delete",
  1684                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1685                                               @profile
  1686                                               def delete(self, gateway, fip):
  1687         1          3.0      3.0      0.0          fip = (fip if isinstance(fip, GCPFloatingIP)
  1688         1     426432.0 426432.0     10.4                 else self.get(gateway, fip))
  1689         1          2.0      2.0      0.0          project_name = self.provider.project_name
  1690                                                   # First, delete the forwarding rule, if there is any.
  1691                                                   # pylint:disable=protected-access
  1692         1          1.0      1.0      0.0          if fip._rule:
  1693                                                       response = (self.provider
  1694                                                                   .gcp_compute
  1695                                                                   .forwardingRules()
  1696                                                                   .delete(project=project_name,
  1697                                                                           region=fip.region_name,
  1698                                                                           forwardingRule=fip._rule['name'])
  1699                                                                   .execute())
  1700                                                       self.provider.wait_for_operation(response,
  1701                                                                                        region=fip.region_name)
  1702                                           
  1703                                                   # Release the address.
  1704         1       3558.0   3558.0      0.1          response = (self.provider
  1705                                                               .gcp_compute
  1706                                                               .addresses()
  1707         1          1.0      1.0      0.0                      .delete(project=project_name,
  1708         1        329.0    329.0      0.0                              region=fip.region_name,
  1709         1     815837.0 815837.0     19.8                              address=fip._ip['name'])
  1710                                                               .execute())
  1711         1         10.0     10.0      0.0          self.provider.wait_for_operation(response,
  1712         1    2867653.0 2867653.0     69.7                                           region=fip.region_name)

Total time: 3.9701 s
Function: get at line 786

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   786                                               @dispatch(event="provider.networking.networks.get",
   787                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   788                                               @profile
   789                                               def get(self, network_id):
   790        14    3969650.0 283546.4    100.0          network = self.provider.get_resource('networks', network_id)
   791        14        452.0     32.3      0.0          return GCPNetwork(self.provider, network) if network else None

Total time: 3.07852 s
Function: create at line 1667

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1667                                               @dispatch(event="provider.networking.floating_ips.create",
  1668                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1669                                               @profile
  1670                                               def create(self, gateway):
  1671         1          4.0      4.0      0.0          region_name = self.provider.region_name
  1672         1         50.0     50.0      0.0          ip_name = 'ip-{0}'.format(uuid.uuid4())
  1673         1       4379.0   4379.0      0.1          response = (self.provider
  1674                                                               .gcp_compute
  1675                                                               .addresses()
  1676         1          2.0      2.0      0.0                      .insert(project=self.provider.project_name,
  1677         1          0.0      0.0      0.0                              region=region_name,
  1678         1     899000.0 899000.0     29.2                              body={'name': ip_name})
  1679                                                               .execute())
  1680         1    1923116.0 1923116.0     62.5          self.provider.wait_for_operation(response, region=region_name)
  1681         1     251972.0 251972.0      8.2          return self.get(gateway, ip_name)

Total time: 3.00229 s
Function: refresh at line 1390

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1390                                               @profile
  1391                                               def refresh(self):
  1392                                                   # pylint:disable=protected-access
  1393         2    1773439.0 886719.5     59.1          fip = self._provider.networking._floating_ips.get(None, self.id)
  1394                                                   # pylint:disable=protected-access
  1395         2          6.0      3.0      0.0          self._ip = fip._ip
  1396         1    1228844.0 1228844.0     40.9          self._process_ip_users()

Total time: 2.73658 s
Function: delete at line 704

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   704                                               @dispatch(event="provider.compute.instances.delete",
   705                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   706                                               @profile
   707                                               def delete(self, instance):
   708         4          8.0      2.0      0.0          instance = (instance if isinstance(instance, GCPInstance) else
   709                                                               self.get(instance))
   710         4          4.0      1.0      0.0          if instance:
   711         4      84021.0  21005.2      3.1              (self._provider
   712                                                        .gcp_compute
   713                                                        .instances()
   714         4         23.0      5.8      0.0               .delete(project=self.provider.project_name,
   715         4       1570.0    392.5      0.1                       zone=instance.zone_name,
   716         4    2650951.0 662737.8     96.9                       instance=instance.name)
   717                                                        .execute())

Total time: 2.43989 s
Function: get at line 1637

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1637                                               @dispatch(event="provider.networking.floating_ips.get",
  1638                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1639                                               @profile
  1640                                               def get(self, gateway, floating_ip_id):
  1641         4    1385894.0 346473.5     56.8          fip = self.provider.get_resource('addresses', floating_ip_id)
  1642                                                   return (GCPFloatingIP(self.provider, fip)
  1643         4    1053999.0 263499.8     43.2                  if fip else None)

Total time: 1.69472 s
Function: find_by_network_and_tags at line 230

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   230                                               @profile
   231                                               def find_by_network_and_tags(self, network_name, tags):
   232                                                   """
   233                                                   Finds non-empty VM firewalls by network name and VM firewall names
   234                                                   (tags). If no matching VM firewall is found, an empty list is returned.
   235                                                   """
   236         6          5.0      0.8      0.0          vm_firewalls = []
   237        42      10859.0    258.5      0.6          for tag, net_name in self._delegate.tag_networks:
   238        36         23.0      0.6      0.0              if network_name != net_name:
   239        14         10.0      0.7      0.0                  continue
   240        22         13.0      0.6      0.0              if tag not in tags:
   241        16          8.0      0.5      0.0                  continue
   242         6    1683662.0 280610.3     99.3              network = self.provider.networking.networks.get(net_name)
   243         6          7.0      1.2      0.0              vm_firewalls.append(
   244         6        126.0     21.0      0.0                  GCPVMFirewall(self._delegate, tag, network))
   245         6          4.0      0.7      0.0          return vm_firewalls

Total time: 1.44253 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         4         16.0      4.0      0.0          region = self.provider.get_resource('regions', region_id,
   387         4    1442438.0 360609.5    100.0                                              region=region_id)
   388         4         80.0     20.0      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 1.366 s
Function: get at line 435

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   435                                               @profile
   436                                               def get(self, image_id):
   437                                                   """
   438                                                   Returns an Image given its id
   439                                                   """
   440         5    1365888.0 273177.6    100.0          image = self.provider.get_resource('images', image_id)
   441         5         12.0      2.4      0.0          if image:
   442         5        102.0     20.4      0.0              return GCPMachineImage(self.provider, image)
   443                                                   self._retrieve_public_images()
   444                                                   for public_image in self._public_images:
   445                                                       if public_image.id == image_id or public_image.name == image_id:
   446                                                           return public_image
   447                                                   return None

Total time: 1.00271 s
Function: delete at line 1410

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1410                                               @dispatch(event="provider.storage.snapshots.delete",
  1411                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1412                                               @profile
  1413                                               def delete(self, snapshot):
  1414         1          2.0      2.0      0.0          snapshot = (snapshot if isinstance(snapshot, GCPSnapshot)
  1415                                                               else self.get(snapshot))
  1416         1          0.0      0.0      0.0          if snapshot:
  1417         1       4602.0   4602.0      0.5              (self.provider
  1418                                                            .gcp_compute
  1419                                                            .snapshots()
  1420         1          3.0      3.0      0.0                   .delete(project=self.provider.project_name,
  1421         1     998101.0 998101.0     99.5                           snapshot=snapshot.name)
  1422                                                            .execute())

Total time: 0.96113 s
Function: list at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @dispatch(event="provider.compute.instances.list",
   678                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   679                                               @profile
   680                                               def list(self, limit=None, marker=None):
   681                                                   """
   682                                                   List all instances.
   683                                                   """
   684                                                   # For GCP API, Acceptable values are 0 to 500, inclusive.
   685                                                   # (Default: 500).
   686         5          7.0      1.4      0.0          max_result = limit if limit is not None and limit < 500 else 500
   687         5     105195.0  21039.0     10.9          response = (self.provider
   688                                                                   .gcp_compute
   689                                                                   .instances()
   690         5         24.0      4.8      0.0                          .list(project=self.provider.project_name,
   691         5          5.0      1.0      0.0                                zone=self.provider.default_zone,
   692         5          2.0      0.4      0.0                                maxResults=max_result,
   693         5     855671.0 171134.2     89.0                                pageToken=marker)
   694                                                                   .execute())
   695         5         20.0      4.0      0.0          instances = [GCPInstance(self.provider, inst)
   696         5        124.0     24.8      0.0                       for inst in response.get('items', [])]
   697         5         11.0      2.2      0.0          if len(instances) > max_result:
   698                                                       log.warning('Expected at most %d results; got %d',
   699                                                                   max_result, len(instances))
   700         5          9.0      1.8      0.0          return ServerPagedResultList('nextPageToken' in response,
   701         5          9.0      1.8      0.0                                       response.get('nextPageToken'),
   702         5         53.0     10.6      0.0                                       False, data=instances)

Total time: 0.864771 s
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
  1010         4          5.0      1.2      0.0          filter = None
  1011         4          5.0      1.2      0.0          if network is not None:
  1012         1          2.0      2.0      0.0              network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014         1          4.0      4.0      0.0              filter = 'network eq %s' % network.resource_url
  1015         4          2.0      0.5      0.0          if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018         4         10.0      2.5      0.0              region_name = self.provider.region_name
  1019         4          1.0      0.2      0.0          subnets = []
  1020         4      37389.0   9347.2      4.3          response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023         4         11.0      2.8      0.0                          .list(project=self.provider.project_name,
  1024         4          4.0      1.0      0.0                                region=region_name,
  1025         4     826917.0 206729.2     95.6                                filter=filter)
  1026                                                                   .execute())
  1027        26         38.0      1.5      0.0          for subnet in response.get('items', []):
  1028        22        185.0      8.4      0.0              subnets.append(GCPSubnet(self.provider, subnet))
  1029         4          8.0      2.0      0.0          return ClientPagedResultList(self.provider, subnets,
  1030         4        190.0     47.5      0.0                                       limit=limit, marker=marker)

Total time: 0.790459 s
Function: get at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @dispatch(event="provider.compute.vm_types.get",
   342                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   343                                               @profile
   344                                               def get(self, vm_type_id):
   345         5     790367.0 158073.4    100.0          vm_type = self.provider.get_resource('machineTypes', vm_type_id)
   346         5         92.0     18.4      0.0          return GCPVMType(self.provider, vm_type) if vm_type else None

Total time: 0.680198 s
Function: get at line 1322

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1322                                               @dispatch(event="provider.storage.snapshots.get",
  1323                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1324                                               @profile
  1325                                               def get(self, snapshot_id):
  1326         2     680154.0 340077.0    100.0          snapshot = self.provider.get_resource('snapshots', snapshot_id)
  1327         2         44.0     22.0      0.0          return GCPSnapshot(self.provider, snapshot) if snapshot else None

Total time: 0.672234 s
Function: get at line 996

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   996                                               @dispatch(event="provider.networking.subnets.get",
   997                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
   998                                               @profile
   999                                               def get(self, subnet_id):
  1000         2     672214.0 336107.0    100.0          subnet = self.provider.get_resource('subnetworks', subnet_id)
  1001         2         20.0     10.0      0.0          return GCPSubnet(self.provider, subnet) if subnet else None

Total time: 0.431264 s
Function: refresh at line 1880

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1880                                               @profile
  1881                                               def refresh(self):
  1882                                                   """
  1883                                                   Refreshes the state of this snapshot by re-querying the cloud provider
  1884                                                   for its latest state.
  1885                                                   """
  1886         1     431258.0 431258.0    100.0          snap = self._provider.storage.snapshots.get(self.id)
  1887         1          1.0      1.0      0.0          if snap:
  1888                                                       # pylint:disable=protected-access
  1889         1          5.0      5.0      0.0              self._snapshot = snap._snapshot
  1890                                                   else:
  1891                                                       # snapshot no longer exists
  1892                                                       self._snapshot['status'] = SnapshotState.UNKNOWN

Total time: 0.405631 s
Function: delete at line 1303

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1303                                               @dispatch(event="provider.storage.volumes.delete",
  1304                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1305                                               @profile
  1306                                               def delete(self, volume):
  1307         1          2.0      2.0      0.0          volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
  1308         1          1.0      1.0      0.0          if volume:
  1309         1       8432.0   8432.0      2.1              (self._provider.gcp_compute
  1310                                                                      .disks()
  1311         1          3.0      3.0      0.0                             .delete(project=self.provider.project_name,
  1312         1        475.0    475.0      0.1                                     zone=volume.zone_name,
  1313         1     396718.0 396718.0     97.8                                     disk=volume.name)
  1314                                                                      .execute())

Total time: 0.397005 s
Function: get at line 893

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   893                                               @dispatch(event="provider.networking.routers.get",
   894                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   895                                               @profile
   896                                               def get(self, router_id):
   897         1          3.0      3.0      0.0          router = self.provider.get_resource(
   898         1     396986.0 396986.0    100.0              'routers', router_id, region=self.provider.region_name)
   899         1         16.0     16.0      0.0          return GCPRouter(self.provider, router) if router else None

Total time: 0.38114 s
Function: find at line 656

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   656                                               @dispatch(event="provider.compute.instances.find",
   657                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   658                                               @profile
   659                                               def find(self, limit=None, marker=None, **kwargs):
   660                                                   """
   661                                                   Searches for instances by instance label.
   662                                                   :return: a list of Instance objects
   663                                                   """
   664         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
   665                                           
   666                                                   # All kwargs should have been popped at this time.
   667         3          3.0      1.0      0.0          if len(kwargs) > 0:
   668         1          1.0      1.0      0.0              raise InvalidParamException(
   669         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   670         1         16.0     16.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   671                                           
   672         2     381024.0 190512.0    100.0          instances = [instance for instance in self.list()
   673                                                                if instance.label == label]
   674         2          6.0      3.0      0.0          return ClientPagedResultList(self.provider, instances,
   675         2         83.0     41.5      0.0                                       limit=limit, marker=marker)

Total time: 0.348102 s
Function: find at line 348

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   348                                               @dispatch(event="provider.compute.vm_types.find",
   349                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   350                                               @profile
   351                                               def find(self, **kwargs):
   352         2          2.0      1.0      0.0          matched_inst_types = []
   353        58     347756.0   5995.8     99.9          for inst_type in self.instance_data:
   354        56         43.0      0.8      0.0              is_match = True
   355        58         59.0      1.0      0.0              for key, value in kwargs.items():
   356        56         38.0      0.7      0.0                  if key not in inst_type:
   357                                                               raise InvalidParamException(
   358                                                                   "Unrecognised parameters for search: %s." % key)
   359        56         52.0      0.9      0.0                  if inst_type.get(key) != value:
   360        54         38.0      0.7      0.0                      is_match = False
   361        54         37.0      0.7      0.0                      break
   362        56         36.0      0.6      0.0              if is_match:
   363         2          2.0      1.0      0.0                  matched_inst_types.append(
   364         2         37.0     18.5      0.0                      GCPVMType(self.provider, inst_type))
   365         2          2.0      1.0      0.0          return matched_inst_types

Total time: 0.332845 s
Function: refresh at line 1603

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1603                                               @profile
  1604                                               def refresh(self):
  1605         1     332840.0 332840.0    100.0          subnet = self._provider.networking.subnets.get(self.id)
  1606         1          1.0      1.0      0.0          if subnet:
  1607                                                       # pylint:disable=protected-access
  1608                                                       self._subnet = subnet._subnet
  1609                                                   else:
  1610                                                       # subnet no longer exists
  1611         1          4.0      4.0      0.0              self._subnet['status'] = SubnetState.UNKNOWN

Total time: 0.258014 s
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342         1     258010.0 258010.0    100.0          net = self._provider.networking.networks.get(self.id)
  1343         1          1.0      1.0      0.0          if net:
  1344                                                       # pylint:disable=protected-access
  1345                                                       self._network = net._network
  1346                                                   else:
  1347                                                       # network no longer exists
  1348         1          3.0      3.0      0.0              self._network['status'] = NetworkState.UNKNOWN

Total time: 0.230138 s
Function: get at line 91

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    91                                               @dispatch(event="provider.security.key_pairs.get",
    92                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    93                                               @profile
    94                                               def get(self, key_pair_id):
    95                                                   """
    96                                                   Returns a KeyPair given its ID.
    97                                                   """
    98         4     230124.0  57531.0    100.0          for kp in self:
    99         4          8.0      2.0      0.0              if kp.id == key_pair_id:
   100         1          6.0      6.0      0.0                  return kp
   101                                                   else:
   102                                                       return None

Total time: 0.22026 s
Function: list at line 104

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   104                                               @dispatch(event="provider.security.key_pairs.list",
   105                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   106                                               @profile
   107                                               def list(self, limit=None, marker=None):
   108         1          1.0      1.0      0.0          key_pairs = []
   109         1          1.0      1.0      0.0          for item in helpers.find_matching_metadata_items(
   110         5     220108.0  44021.6     99.9                  self.provider, GCPKeyPair.KP_TAG_REGEX):
   111         4         60.0     15.0      0.0              metadata_value = json.loads(item['value'])
   112         4         15.0      3.8      0.0              kp_info = GCPKeyPair.GCPKeyInfo(**metadata_value)
   113         4         36.0      9.0      0.0              key_pairs.append(GCPKeyPair(self.provider, kp_info))
   114         1          2.0      2.0      0.0          return ClientPagedResultList(self.provider, key_pairs,
   115         1         37.0     37.0      0.0                                       limit=limit, marker=marker)

Total time: 0.024806 s
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125         2          8.0      4.0      0.0          obj_list = firewall.rules
   126         2          1.0      0.5      0.0          filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127         2          2.0      1.0      0.0                     'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128         2      24757.0  12378.5     99.8          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129         2         38.0     19.0      0.2          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.015576 s
Function: list at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   255                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   256                                               @profile
   257                                               def list(self, firewall, limit=None, marker=None):
   258         6          8.0      1.3      0.1          rules = []
   259         6         18.0      3.0      0.1          for fw in firewall.delegate.iter_firewalls(
   260        12       1497.0    124.8      9.6                  firewall.name, firewall.network.name):
   261         6       8162.0   1360.3     52.4              rule = GCPVMFirewallRule(firewall, fw['id'])
   262         6       5667.0    944.5     36.4              if rule.is_dummy_rule():
   263         6         11.0      1.8      0.1                  self._dummy_rule = rule
   264                                                       else:
   265                                                           rules.append(rule)
   266         6         15.0      2.5      0.1          return ClientPagedResultList(self.provider, rules,
   267         6        198.0     33.0      1.3                                       limit=limit, marker=marker)

Total time: 2e-05 s
Function: create_launch_config at line 719

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   719                                               @profile
   720                                               def create_launch_config(self):
   721         2         20.0     10.0    100.0          return GCPLaunchConfig(self.provider)

Total time: 5e-06 s
Function: get_or_create at line 1610

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1610                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1611                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1612                                               @profile
  1613                                               def get_or_create(self, network):
  1614         4          5.0      1.2    100.0          return self._default_internet_gateway

