cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase


Test output
 ......
----------------------------------------------------------------------
Ran 6 tests in 294.605s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 55.711 s
Function: create at line 437

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   437                                               @dispatch(event="provider.storage.snapshots.create",
   438                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   439                                               @profile
   440                                               def create(self, label, volume, description=None):
   441        11        122.0     11.1      0.0          AWSSnapshot.assert_valid_resource_label(label)
   442         1          9.0      9.0      0.0          volume_id = volume.id if isinstance(volume, AWSVolume) else volume
   443                                           
   444         1     211438.0 211438.0      0.4          cb_snap = self.svc.create('create_snapshot', VolumeId=volume_id)
   445                                                   # Wait until ready to tag instance
   446         1   55327837.0 55327837.0     99.3          cb_snap.wait_till_ready()
   447         1      97826.0  97826.0      0.2          cb_snap.label = label
   448         1      73762.0  73762.0      0.1          if cb_snap.description:
   449                                                       cb_snap.description = description
   450         1          1.0      1.0      0.0          return cb_snap

Total time: 53.2855 s
Function: create at line 369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   369                                               @dispatch(event="provider.storage.volumes.create",
   370                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   371                                               @profile
   372                                               def create(self, label, size, zone, snapshot=None, description=None):
   373        17        217.0     12.8      0.0          AWSVolume.assert_valid_resource_label(label)
   374         7         16.0      2.3      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   375         7          7.0      1.0      0.0          snapshot_id = snapshot.id if isinstance(
   376         7         12.0      1.7      0.0              snapshot, AWSSnapshot) and snapshot else snapshot
   377                                           
   378         7         22.0      3.1      0.0          cb_vol = self.svc.create('create_volume', Size=size,
   379         7          3.0      0.4      0.0                                   AvailabilityZone=zone_id,
   380         7    2239880.0 319982.9      4.2                                   SnapshotId=snapshot_id)
   381                                                   # Wait until ready to tag instance
   382         7   50134821.0 7162117.3     94.1          cb_vol.wait_till_ready()
   383         7     805867.0 115123.9      1.5          cb_vol.label = label
   384         7         11.0      1.6      0.0          if description:
   385         1     104626.0 104626.0      0.2              cb_vol.description = description
   386         7          6.0      0.9      0.0          return cb_vol

Total time: 14.523 s
Function: refresh at line 376

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   376                                               @profile
   377                                               def refresh(self):
   378       103        528.0      5.1      0.0          try:
   379       103   14522148.0 140991.7    100.0              self._ec2_instance.reload()
   380       103        279.0      2.7      0.0              self._unknown_state = False
   381                                                   except ClientError:
   382                                                       # The instance no longer exists and cannot be refreshed.
   383                                                       # set the state to unknown
   384                                                       self._unknown_state = True

Total time: 7.99197 s
Function: list at line 430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   430                                               @dispatch(event="provider.storage.snapshots.list",
   431                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   432                                               @profile
   433                                               def list(self, limit=None, marker=None):
   434        26         52.0      2.0      0.0          return self.svc.list(limit=limit, marker=marker,
   435        26    7991920.0 307381.5    100.0                               OwnerIds=['self'])

Total time: 7.74737 s
Function: refresh at line 509

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   509                                               @profile
   510                                               def refresh(self):
   511        67        272.0      4.1      0.0          try:
   512        67    7746879.0 115625.1    100.0              self._volume.reload()
   513        65        170.0      2.6      0.0              self._unknown_state = False
   514         2          5.0      2.5      0.0          except ClientError:
   515                                                       # The volume no longer exists and cannot be refreshed.
   516                                                       # set the status to unknown
   517         2         42.0     21.0      0.0              self._unknown_state = True

Total time: 5.26941 s
Function: refresh at line 593

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   593                                               @profile
   594                                               def refresh(self):
   595        60        239.0      4.0      0.0          try:
   596        60    5268834.0  87813.9    100.0              self._snapshot.reload()
   597        58        286.0      4.9      0.0              self._unknown_state = False
   598         2          6.0      3.0      0.0          except ClientError:
   599                                                       # The snapshot no longer exists and cannot be refreshed.
   600                                                       # set the status to unknown
   601         2         45.0     22.5      0.0              self._unknown_state = True

Total time: 3.15817 s
Function: create at line 769

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   769                                               @dispatch(event="provider.compute.instances.create",
   770                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   771                                               @profile
   772                                               def create(self, label, image, vm_type, subnet, zone,
   773                                                          key_pair=None, vm_firewalls=None, user_data=None,
   774                                                          launch_config=None, **kwargs):
   775         2         24.0     12.0      0.0          AWSInstance.assert_valid_resource_label(label)
   776         2          6.0      3.0      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   777                                                   vm_size = vm_type.id if \
   778         2          3.0      1.5      0.0              isinstance(vm_type, VMType) else vm_type
   779                                                   subnet = (self.provider.networking.subnets.get(subnet)
   780         2          5.0      2.5      0.0                    if isinstance(subnet, str) else subnet)
   781         2          2.0      1.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   782         2          2.0      1.0      0.0          key_pair_name = key_pair.name if isinstance(
   783         2          2.0      1.0      0.0              key_pair,
   784         2          2.0      1.0      0.0              KeyPair) else key_pair
   785         2          2.0      1.0      0.0          if launch_config:
   786                                                       bdm = self._process_block_device_mappings(launch_config)
   787                                                   else:
   788         2          2.0      1.0      0.0              bdm = None
   789                                           
   790                                                   subnet_id, zone_id, vm_firewall_ids = \
   791         2         56.0     28.0      0.0              self._resolve_launch_options(subnet, zone_id, vm_firewalls)
   792                                           
   793         2          3.0      1.5      0.0          placement = {'AvailabilityZone': zone_id} if zone_id else None
   794         2          7.0      3.5      0.0          inst = self.svc.create('create_instances',
   795         2          2.0      1.0      0.0                                 ImageId=image_id,
   796         2          1.0      0.5      0.0                                 MinCount=1,
   797         2          1.0      0.5      0.0                                 MaxCount=1,
   798         2          2.0      1.0      0.0                                 KeyName=key_pair_name,
   799         2          2.0      1.0      0.0                                 SecurityGroupIds=vm_firewall_ids or None,
   800         2          4.0      2.0      0.0                                 UserData=str(user_data) or None,
   801         2          2.0      1.0      0.0                                 InstanceType=vm_size,
   802         2          1.0      0.5      0.0                                 Placement=placement,
   803         2          2.0      1.0      0.0                                 BlockDeviceMappings=bdm,
   804         2    2220846.0 1110423.0     70.3                                 SubnetId=subnet_id
   805                                                                          )
   806         2          7.0      3.5      0.0          if inst and len(inst) == 1:
   807                                                       # Wait until the resource exists
   808                                                       # pylint:disable=protected-access
   809         2     460793.0 230396.5     14.6              inst[0]._wait_till_exists()
   810                                                       # Tag the instance w/ the name
   811         2     476390.0 238195.0     15.1              inst[0].label = label
   812         2          4.0      2.0      0.0              return inst[0]
   813                                                   raise ValueError(
   814                                                       'Expected a single object response, got a list: %s' % inst)

Total time: 2.06389 s
Function: find at line 412

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   412                                               @dispatch(event="provider.storage.snapshots.find",
   413                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   414                                               @profile
   415                                               def find(self, **kwargs):
   416                                                   # Filter by description or label
   417         6         11.0      1.8      0.0          label = kwargs.get('label', None)
   418                                           
   419         6          5.0      0.8      0.0          obj_list = []
   420         6          2.0      0.3      0.0          if label:
   421         4         30.0      7.5      0.0              log.debug("Searching for AWS Snapshot with label %s", label)
   422         4          7.0      1.8      0.0              obj_list.extend(self.svc.find(filter_name='tag:Name',
   423         4          2.0      0.5      0.0                                            filter_value=label,
   424         4     369924.0  92481.0     17.9                                            OwnerIds=['self']))
   425                                                   else:
   426         2    1691969.0 845984.5     82.0              obj_list = list(self)
   427         6         11.0      1.8      0.0          filters = ['label']
   428         6       1928.0    321.3      0.1          return cb_helpers.generic_find(filters, kwargs, obj_list)

Total time: 1.35729 s
Function: label at line 426

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   426                                               @label.setter
   427                                               # pylint:disable=arguments-differ
   428                                               @profile
   429                                               def label(self, value):
   430        19        216.0     11.4      0.0          self.assert_valid_resource_label(value)
   431        11    1357074.0 123370.4    100.0          self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 1.1909 s
Function: delete at line 388

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   388                                               @dispatch(event="provider.storage.volumes.delete",
   389                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   390                                               @profile
   391                                               def delete(self, vol):
   392         7         21.0      3.0      0.0          volume = vol if isinstance(vol, AWSVolume) else self.get(vol)
   393         7          7.0      1.0      0.0          if volume:
   394                                                       # pylint:disable=protected-access
   395         7    1190873.0 170124.7    100.0              volume._volume.delete()

Total time: 0.799853 s
Function: label at line 552

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   552                                               @label.setter
   553                                               # pylint:disable=arguments-differ
   554                                               @profile
   555                                               def label(self, value):
   556        24        278.0     11.6      0.0          self.assert_valid_resource_label(value)
   557         8         12.0      1.5      0.0          self._snapshot.create_tags(Tags=[{'Key': 'Name',
   558         8     799563.0  99945.4    100.0                                            'Value': value or ""}])

Total time: 0.727776 s
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105         2          8.0      4.0      0.0          zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
  1106                                           
  1107                                                   # # Look for provider default subnet in current zone
  1108                                                   # if zone_name:
  1109                                                   #     snl = self.svc.find('availabilityZone', zone_name)
  1110                                                   #
  1111                                                   # else:
  1112                                                   #     snl = self.svc.list()
  1113                                                   #     # Find first available default subnet by sorted order
  1114                                                   #     # of availability zone. Prefer zone us-east-1a over 1e,
  1115                                                   #     # because newer zones tend to have less compatibility
  1116                                                   #     # with different instance types (e.g. c5.large not available
  1117                                                   #     # on us-east-1e as of 14 Dec. 2017).
  1118                                                   #     # pylint:disable=protected-access
  1119                                                   #     snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1120                                                   #
  1121                                                   # for sn in snl:
  1122                                                   #     # pylint:disable=protected-access
  1123                                                   #     if sn._subnet.default_for_az:
  1124                                                   #         return sn
  1125                                           
  1126                                                   # If no provider-default subnet has been found, look for
  1127                                                   # cloudbridge-default by label. We suffix labels by availability zone,
  1128                                                   # thus we add the wildcard for the regular expression to find the
  1129                                                   # subnet
  1130         2     727687.0 363843.5    100.0          snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132         2          4.0      2.0      0.0          if snl:
  1133                                                       # pylint:disable=protected-access
  1134         2         33.0     16.5      0.0              snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135         2          3.0      1.5      0.0              if not zone_name:
  1136                                                           return snl[0]
  1137         2          2.0      1.0      0.0              for subnet in snl:
  1138         2         37.0     18.5      0.0                  if subnet.zone.name == zone_name:
  1139         2          2.0      1.0      0.0                      return subnet
  1140                                           
  1141                                                   # No default Subnet exists, try to create a CloudBridge-specific
  1142                                                   # subnet. This involves creating the network, subnets, internet
  1143                                                   # gateway, and connecting it all together so that the network has
  1144                                                   # Internet connectivity.
  1145                                           
  1146                                                   # Check if a default net already exists and get it or create on
  1147                                                   default_net = self.provider.networking.networks.get_or_create_default()
  1148                                           
  1149                                                   # Get/create an internet gateway for the default network and a
  1150                                                   # corresponding router if it does not already exist.
  1151                                                   # NOTE: Comment this out because the docs instruct users to setup
  1152                                                   # network connectivity manually. There's a bit of discrepancy here
  1153                                                   # though because the provider-default network will have Internet
  1154                                                   # connectivity (unlike the CloudBridge-default network with this
  1155                                                   # being commented) and is hence left in the codebase.
  1156                                                   # default_gtw = default_net.gateways.get_or_create()
  1157                                                   # router_label = "{0}-router".format(
  1158                                                   #   AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
  1159                                                   # default_routers = self.provider.networking.routers.find(
  1160                                                   #     label=router_label)
  1161                                                   # if len(default_routers) == 0:
  1162                                                   #     default_router = self.provider.networking.routers.create(
  1163                                                   #         router_label, default_net)
  1164                                                   #     default_router.attach_gateway(default_gtw)
  1165                                                   # else:
  1166                                                   #     default_router = default_routers[0]
  1167                                           
  1168                                                   # Create a subnet in each of the region's zones
  1169                                                   region = self.provider.compute.regions.get(self.provider.region_name)
  1170                                                   default_sn = None
  1171                                           
  1172                                                   # Determine how many subnets we'll need for the default network and the
  1173                                                   # number of available zones. We need to derive a non-overlapping
  1174                                                   # network size for each subnet within the parent net so figure those
  1175                                                   # subnets here. `<net>.subnets` method will do this but we need to give
  1176                                                   # it a prefix. Determining that prefix depends on the size of the
  1177                                                   # network and should be incorporate the number of zones. So iterate
  1178                                                   # over potential number of subnets until enough can be created to
  1179                                                   # accommodate the number of available zones. That is where the fixed
  1180                                                   # number comes from in the for loop as that many iterations will yield
  1181                                                   # more potential subnets than any region has zones.
  1182                                                   ip_net = ipaddress.ip_network(AWSNetwork.CB_DEFAULT_IPV4RANGE)
  1183                                                   for x in range(5):
  1184                                                       if len(region.zones) <= len(list(ip_net.subnets(
  1185                                                               prefixlen_diff=x))):
  1186                                                           prefixlen_diff = x
  1187                                                           break
  1188                                                   subnets = list(ip_net.subnets(prefixlen_diff=prefixlen_diff))
  1189                                           
  1190                                                   for i, z in reversed(list(enumerate(region.zones))):
  1191                                                       sn_label = "{0}-{1}".format(AWSSubnet.CB_DEFAULT_SUBNET_LABEL,
  1192                                                                                   z.id[-1])
  1193                                                       log.info("Creating a default CloudBridge subnet %s: %s" %
  1194                                                                (sn_label, str(subnets[i])))
  1195                                                       sn = self.create(sn_label, default_net, str(subnets[i]), z)
  1196                                                       # Create a route table entry between the SN and the inet gateway
  1197                                                       # See note above about why this is commented
  1198                                                       # default_router.attach_subnet(sn)
  1199                                                       if zone and zone_name == z.name:
  1200                                                           default_sn = sn
  1201                                                   # No specific zone was supplied; return the last created subnet
  1202                                                   # The list was originally reversed to have the last subnet be in zone a
  1203                                                   if not default_sn:
  1204                                                       default_sn = sn
  1205                                                   return default_sn

Total time: 0.67235 s
Function: delete at line 452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   452                                               @dispatch(event="provider.storage.snapshots.delete",
   453                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   454                                               @profile
   455                                               def delete(self, snapshot):
   456         3          6.0      2.0      0.0          snapshot = (snapshot if isinstance(snapshot, AWSSnapshot) else
   457                                                               self.get(snapshot))
   458         3          9.0      3.0      0.0          if snapshot:
   459                                                       # pylint:disable=protected-access
   460         3     672335.0 224111.7    100.0              snapshot._snapshot.delete()

Total time: 0.667217 s
Function: list at line 363

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   363                                               @dispatch(event="provider.storage.volumes.list",
   364                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   365                                               @profile
   366                                               def list(self, limit=None, marker=None):
   367         4     667217.0 166804.2    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 0.660379 s
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065         2          2.0      1.0      0.0          label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068         2          2.0      1.0      0.0          if len(kwargs) > 0:
  1069                                                       raise InvalidParamException(
  1070                                                           "Unrecognised parameters for search: %s. Supported "
  1071                                                           "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073         2         24.0     12.0      0.0          log.debug("Searching for AWS Subnet Service %s", label)
  1074         2     660351.0 330175.5    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.615225 s
Function: delete at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @dispatch(event="provider.compute.instances.delete",
   843                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   844                                               @profile
   845                                               def delete(self, instance):
   846         2          4.0      2.0      0.0          aws_inst = (instance if isinstance(instance, AWSInstance) else
   847                                                               self.get(instance))
   848         2          2.0      1.0      0.0          if aws_inst:
   849                                                       # pylint:disable=protected-access
   850         2     615219.0 307609.5    100.0              aws_inst._ec2_instance.terminate()

Total time: 0.476349 s
Function: label at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @label.setter
   255                                               # pylint:disable=arguments-differ
   256                                               @profile
   257                                               def label(self, value):
   258         2         17.0      8.5      0.0          self.assert_valid_resource_label(value)
   259         2          7.0      3.5      0.0          self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
   260         2     476325.0 238162.5    100.0                                                'Value': value or ""}])

Total time: 0.303705 s
Function: get at line 406

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   406                                               @dispatch(event="provider.storage.snapshots.get",
   407                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   408                                               @profile
   409                                               def get(self, snapshot_id):
   410         4     303705.0  75926.2    100.0          return self.svc.get(snapshot_id)

Total time: 0.265743 s
Function: find at line 348

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   348                                               @dispatch(event="provider.storage.volumes.find",
   349                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   350                                               @profile
   351                                               def find(self, **kwargs):
   352         3         21.0      7.0      0.0          label = kwargs.pop('label', None)
   353                                           
   354                                                   # All kwargs should have been popped at this time.
   355         3          4.0      1.3      0.0          if len(kwargs) > 0:
   356         1          1.0      1.0      0.0              raise InvalidParamException(
   357         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   358         1         16.0     16.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   359                                           
   360         2         15.0      7.5      0.0          log.debug("Searching for AWS Volume Service %s", label)
   361         2     265685.0 132842.5    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.163409 s
Function: get at line 342

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   342                                               @dispatch(event="provider.storage.volumes.get",
   343                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   344                                               @profile
   345                                               def get(self, volume_id):
   346         2     163409.0  81704.5    100.0          return self.svc.get(volume_id)

Total time: 0.104892 s
Function: description at line 564

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   564                                               @description.setter
   565                                               @profile
   566                                               def description(self, value):
   567         1          2.0      2.0      0.0          self._snapshot.create_tags(Tags=[{
   568         1     104890.0 104890.0    100.0              'Key': 'Description', 'Value': value or ""}])

Total time: 0.104612 s
Function: description at line 437

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   437                                               @description.setter
   438                                               @profile
   439                                               def description(self, value):
   440         1          2.0      2.0      0.0          self._volume.create_tags(Tags=[{'Key': 'Description',
   441         1     104610.0 104610.0    100.0                                          'Value': value or ""}])

