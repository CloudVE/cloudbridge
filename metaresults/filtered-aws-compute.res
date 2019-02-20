cloudbridge.test.test_compute_service.CloudComputeServiceTestCase


Error during cleanup: False is not true : Instance.state must be unknown when refreshing after a delete but got deleted
Error during cleanup: An error occurred (InvalidAllocationID.NotFound) when calling the DescribeAddresses operation: The allocation ID 'eipalloc-0ee614962c6e91a84' does not exist
Test output
 ......
----------------------------------------------------------------------
Ran 6 tests in 383.400s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 40.1343 s
Function: refresh at line 376

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   376                                               @profile
   377                                               def refresh(self):
   378       308       1184.0      3.8      0.0          try:
   379       308   40132285.0 130299.6    100.0              self._ec2_instance.reload()
   380       308        854.0      2.8      0.0              self._unknown_state = False
   381                                                   except ClientError:
   382                                                       # The instance no longer exists and cannot be refreshed.
   383                                                       # set the state to unknown
   384                                                       self._unknown_state = True

Total time: 8.67415 s
Function: create at line 769

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   769                                               @dispatch(event="provider.compute.instances.create",
   770                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   771                                               @profile
   772                                               def create(self, label, image, vm_type, subnet, zone,
   773                                                          key_pair=None, vm_firewalls=None, user_data=None,
   774                                                          launch_config=None, **kwargs):
   775        14        154.0     11.0      0.0          AWSInstance.assert_valid_resource_label(label)
   776         4          9.0      2.2      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   777                                                   vm_size = vm_type.id if \
   778         4          5.0      1.2      0.0              isinstance(vm_type, VMType) else vm_type
   779                                                   subnet = (self.provider.networking.subnets.get(subnet)
   780         4         10.0      2.5      0.0                    if isinstance(subnet, str) else subnet)
   781         4          4.0      1.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   782         4          3.0      0.8      0.0          key_pair_name = key_pair.name if isinstance(
   783         4          2.0      0.5      0.0              key_pair,
   784         4         17.0      4.2      0.0              KeyPair) else key_pair
   785         4          4.0      1.0      0.0          if launch_config:
   786         1         52.0     52.0      0.0              bdm = self._process_block_device_mappings(launch_config)
   787                                                   else:
   788         3          3.0      1.0      0.0              bdm = None
   789                                           
   790                                                   subnet_id, zone_id, vm_firewall_ids = \
   791         4     218183.0  54545.8      2.5              self._resolve_launch_options(subnet, zone_id, vm_firewalls)
   792                                           
   793         4          6.0      1.5      0.0          placement = {'AvailabilityZone': zone_id} if zone_id else None
   794         4         14.0      3.5      0.0          inst = self.svc.create('create_instances',
   795         4          4.0      1.0      0.0                                 ImageId=image_id,
   796         4          4.0      1.0      0.0                                 MinCount=1,
   797         4          4.0      1.0      0.0                                 MaxCount=1,
   798         4          4.0      1.0      0.0                                 KeyName=key_pair_name,
   799         4          3.0      0.8      0.0                                 SecurityGroupIds=vm_firewall_ids or None,
   800         4          9.0      2.2      0.0                                 UserData=str(user_data) or None,
   801         4          2.0      0.5      0.0                                 InstanceType=vm_size,
   802         4          3.0      0.8      0.0                                 Placement=placement,
   803         4          2.0      0.5      0.0                                 BlockDeviceMappings=bdm,
   804         4    6868958.0 1717239.5     79.2                                 SubnetId=subnet_id
   805                                                                          )
   806         4         11.0      2.8      0.0          if inst and len(inst) == 1:
   807                                                       # Wait until the resource exists
   808                                                       # pylint:disable=protected-access
   809         4     853666.0 213416.5      9.8              inst[0]._wait_till_exists()
   810                                                       # Tag the instance w/ the name
   811         4     733006.0 183251.5      8.5              inst[0].label = label
   812         4          9.0      2.2      0.0              return inst[0]
   813                                                   raise ValueError(
   814                                                       'Expected a single object response, got a list: %s' % inst)

Total time: 5.88847 s
Function: create at line 369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   369                                               @dispatch(event="provider.storage.volumes.create",
   370                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   371                                               @profile
   372                                               def create(self, label, size, zone, snapshot=None, description=None):
   373         1         13.0     13.0      0.0          AWSVolume.assert_valid_resource_label(label)
   374         1          1.0      1.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   375         1          1.0      1.0      0.0          snapshot_id = snapshot.id if isinstance(
   376         1          1.0      1.0      0.0              snapshot, AWSSnapshot) and snapshot else snapshot
   377                                           
   378         1          4.0      4.0      0.0          cb_vol = self.svc.create('create_volume', Size=size,
   379         1          0.0      0.0      0.0                                   AvailabilityZone=zone_id,
   380         1     284030.0 284030.0      4.8                                   SnapshotId=snapshot_id)
   381                                                   # Wait until ready to tag instance
   382         1    5496369.0 5496369.0     93.3          cb_vol.wait_till_ready()
   383         1     108043.0 108043.0      1.8          cb_vol.label = label
   384         1          2.0      2.0      0.0          if description:
   385                                                       cb_vol.description = description
   386         1          1.0      1.0      0.0          return cb_vol

Total time: 2.79839 s
Function: list at line 881

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   881                                               @dispatch(event="provider.compute.vm_types.list",
   882                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   883                                               @profile
   884                                               def list(self, limit=None, marker=None):
   885         6          9.0      1.5      0.0          vm_types = [AWSVMType(self.provider, vm_type)
   886         6    2798173.0 466362.2    100.0                      for vm_type in self.instance_data]
   887         6         11.0      1.8      0.0          return ClientPagedResultList(self.provider, vm_types,
   888         6        202.0     33.7      0.0                                       limit=limit, marker=marker)

Total time: 2.12073 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         5          8.0      1.6      0.0          obj_list = self
   230         5          5.0      1.0      0.0          filters = ['name']
   231         5    2120612.0 424122.4    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         5        101.0     20.2      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 1.404 s
Function: label at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @label.setter
   255                                               # pylint:disable=arguments-differ
   256                                               @profile
   257                                               def label(self, value):
   258        15        184.0     12.3      0.0          self.assert_valid_resource_label(value)
   259         7         14.0      2.0      0.0          self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
   260         7    1403800.0 200542.9    100.0                                                'Value': value or ""}])

Total time: 1.29368 s
Function: list at line 836

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   836                                               @dispatch(event="provider.compute.instances.list",
   837                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   838                                               @profile
   839                                               def list(self, limit=None, marker=None):
   840         9    1293682.0 143742.4    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 1.27073 s
Function: get at line 173

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   173                                               @dispatch(event="provider.security.vm_firewalls.get",
   174                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   175                                               @profile
   176                                               def get(self, vm_firewall_id):
   177        13         99.0      7.6      0.0          log.debug("Getting Firewall Service with the id: %s", vm_firewall_id)
   178        13    1270631.0  97740.8    100.0          return self.svc.get(vm_firewall_id)

Total time: 1.11421 s
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105         3          8.0      2.7      0.0          zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
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
  1130         3    1114076.0 371358.7    100.0          snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132         3          7.0      2.3      0.0          if snl:
  1133                                                       # pylint:disable=protected-access
  1134         3         45.0     15.0      0.0              snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135         3          6.0      2.0      0.0              if not zone_name:
  1136                                                           return snl[0]
  1137         3          4.0      1.3      0.0              for subnet in snl:
  1138         3         58.0     19.3      0.0                  if subnet.zone.name == zone_name:
  1139         3          4.0      1.3      0.0                      return subnet
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

Total time: 1.08196 s
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068         3          4.0      1.3      0.0          if len(kwargs) > 0:
  1069                                                       raise InvalidParamException(
  1070                                                           "Unrecognised parameters for search: %s. Supported "
  1071                                                           "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073         3         26.0      8.7      0.0          log.debug("Searching for AWS Subnet Service %s", label)
  1074         3    1081928.0 360642.7    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.915045 s
Function: create at line 186

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   186                                               @cb_helpers.deprecated_alias(network_id='network')
   187                                               @dispatch(event="provider.security.vm_firewalls.create",
   188                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   189                                               @profile
   190                                               def create(self, label, network, description=None):
   191         2         17.0      8.5      0.0          AWSVMFirewall.assert_valid_resource_label(label)
   192         2         89.0     44.5      0.0          name = AWSVMFirewall._generate_name_from_label(label, 'cb-fw')
   193         2          3.0      1.5      0.0          network_id = network.id if isinstance(network, Network) else network
   194         2          4.0      2.0      0.0          obj = self.svc.create('create_security_group', GroupName=name,
   195         2          1.0      0.5      0.0                                Description=name,
   196         2     382090.0 191045.0     41.8                                VpcId=network_id)
   197         2     274942.0 137471.0     30.0          obj.label = label
   198         2     257897.0 128948.5     28.2          obj.description = description
   199         2          2.0      1.0      0.0          return obj

Total time: 0.875675 s
Function: delete at line 216

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   216                                               @dispatch(event="provider.security.vm_firewalls.delete",
   217                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   218                                               @profile
   219                                               def delete(self, vm_firewall):
   220         2          4.0      2.0      0.0          firewall = (vm_firewall if isinstance(vm_firewall, AWSVMFirewall)
   221                                                               else self.get(vm_firewall))
   222         2          1.0      0.5      0.0          if firewall:
   223                                                       # pylint:disable=protected-access
   224         2     875670.0 437835.0    100.0              firewall._vm_firewall.delete()

Total time: 0.874787 s
Function: create at line 990

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   990                                               @dispatch(event="provider.networking.networks.create",
   991                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   992                                               @profile
   993                                               def create(self, label, cidr_block):
   994         1         13.0     13.0      0.0          AWSNetwork.assert_valid_resource_label(label)
   995                                           
   996         1     261299.0 261299.0     29.9          cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
   997                                                   # Wait until ready to tag instance
   998         1     458052.0 458052.0     52.4          cb_net.wait_till_ready()
   999         1          1.0      1.0      0.0          if label:
  1000         1     155421.0 155421.0     17.8              cb_net.label = label
  1001         1          1.0      1.0      0.0          return cb_net

Total time: 0.826672 s
Function: delete at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @dispatch(event="provider.compute.instances.delete",
   843                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   844                                               @profile
   845                                               def delete(self, instance):
   846         4          8.0      2.0      0.0          aws_inst = (instance if isinstance(instance, AWSInstance) else
   847                                                               self.get(instance))
   848         4          4.0      1.0      0.0          if aws_inst:
   849                                                       # pylint:disable=protected-access
   850         4     826660.0 206665.0    100.0              aws_inst._ec2_instance.terminate()

Total time: 0.725538 s
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222         1          5.0      5.0      0.0          vm_type = (t for t in self if t.id == vm_type_id)
   223         1     725533.0 725533.0    100.0          return next(vm_type, None)

Total time: 0.510209 s
Function: get_or_create at line 1273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1273                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1274                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1275                                               @profile
  1276                                               def get_or_create(self, network):
  1277         1          2.0      2.0      0.0          network_id = network.id if isinstance(
  1278         1          6.0      6.0      0.0              network, AWSNetwork) else network
  1279                                                   # Don't filter by label because it may conflict with at least the
  1280                                                   # default VPC that most accounts have but that network is typically
  1281                                                   # without a name.
  1282         1          2.0      2.0      0.0          gtw = self.svc.find(filter_name='attachment.vpc-id',
  1283         1      97507.0  97507.0     19.1                              filter_value=network_id)
  1284         1          2.0      2.0      0.0          if gtw:
  1285                                                       return gtw[0]  # There can be only one gtw attached to a VPC
  1286                                                   # Gateway does not exist so create one and attach to the supplied net
  1287         1     135340.0 135340.0     26.5          cb_gateway = self.svc.create('create_internet_gateway')
  1288         1          2.0      2.0      0.0          cb_gateway._gateway.create_tags(
  1289         1          1.0      1.0      0.0              Tags=[{'Key': 'Name',
  1290         1     154776.0 154776.0     30.3                     'Value': AWSInternetGateway.CB_DEFAULT_INET_GATEWAY_NAME
  1291                                                              }])
  1292         1     122570.0 122570.0     24.0          cb_gateway._gateway.attach_to_vpc(VpcId=network_id)
  1293         1          1.0      1.0      0.0          return cb_gateway

Total time: 0.478308 s
Function: refresh at line 509

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   509                                               @profile
   510                                               def refresh(self):
   511         5         19.0      3.8      0.0          try:
   512         5     478276.0  95655.2    100.0              self._volume.reload()
   513         5         13.0      2.6      0.0              self._unknown_state = False
   514                                                   except ClientError:
   515                                                       # The volume no longer exists and cannot be refreshed.
   516                                                       # set the status to unknown
   517                                                       self._unknown_state = True

Total time: 0.454137 s
Function: create at line 1076

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1076                                               @dispatch(event="provider.networking.subnets.create",
  1077                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1078                                               @profile
  1079                                               def create(self, label, network, cidr_block, zone):
  1080         1          9.0      9.0      0.0          AWSSubnet.assert_valid_resource_label(label)
  1081         1          1.0      1.0      0.0          zone_name = zone.name if isinstance(
  1082         1          2.0      2.0      0.0              zone, AWSPlacementZone) else zone
  1083                                           
  1084         1          6.0      6.0      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1085                                           
  1086         1          3.0      3.0      0.0          subnet = self.svc.create('create_subnet',
  1087         1          1.0      1.0      0.0                                   VpcId=network_id,
  1088         1          0.0      0.0      0.0                                   CidrBlock=cidr_block,
  1089         1     272957.0 272957.0     60.1                                   AvailabilityZone=zone_name)
  1090         1          2.0      2.0      0.0          if label:
  1091         1     181155.0 181155.0     39.9              subnet.label = label
  1092         1          1.0      1.0      0.0          return subnet

Total time: 0.407957 s
Function: get at line 816

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   816                                               @dispatch(event="provider.compute.instances.get",
   817                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   818                                               @profile
   819                                               def get(self, instance_id):
   820         3     407957.0 135985.7    100.0          return self.svc.get(instance_id)

Total time: 0.401777 s
Function: delete at line 1352

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1352                                               @dispatch(event="provider.networking.floating_ips.delete",
  1353                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1354                                               @profile
  1355                                               def delete(self, gateway, fip):
  1356         1          5.0      5.0      0.0          if isinstance(fip, AWSFloatingIP):
  1357                                                       # pylint:disable=protected-access
  1358                                                       aws_fip = fip._ip
  1359                                                   else:
  1360         1     224850.0 224850.0     56.0              aws_fip = self.svc.get_raw(fip)
  1361         1     176922.0 176922.0     44.0          aws_fip.release()

Total time: 0.38744 s
Function: delete at line 1003

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1003                                               @dispatch(event="provider.networking.networks.delete",
  1004                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1005                                               @profile
  1006                                               def delete(self, network):
  1007         1          3.0      3.0      0.0          network = (network if isinstance(network, AWSNetwork)
  1008                                                              else self.get(network))
  1009         1          1.0      1.0      0.0          if network:
  1010                                                       # pylint:disable=protected-access
  1011         1     387436.0 387436.0    100.0              network._vpc.delete()

Total time: 0.35181 s
Function: refresh at line 1038

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1038                                               @profile
  1039                                               def refresh(self):
  1040         2     351810.0 175905.0    100.0          self._ip.reload()

Total time: 0.340546 s
Function: delete at line 1094

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1094                                               @dispatch(event="provider.networking.subnets.delete",
  1095                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1096                                               @profile
  1097                                               def delete(self, subnet):
  1098         1          2.0      2.0      0.0          sn = subnet if isinstance(subnet, AWSSubnet) else self.get(subnet)
  1099         1          0.0      0.0      0.0          if sn:
  1100                                                       # pylint:disable=protected-access
  1101         1     340544.0 340544.0    100.0              sn._subnet.delete()

Total time: 0.277115 s
Function: create at line 1244

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1244                                               @dispatch(event="provider.networking.routers.create",
  1245                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1246                                               @profile
  1247                                               def create(self, label, network):
  1248         1         12.0     12.0      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1249                                           
  1250         1     134758.0 134758.0     48.6          cb_router = self.svc.create('create_route_table', VpcId=network_id)
  1251         1          1.0      1.0      0.0          if label:
  1252         1     142343.0 142343.0     51.4              cb_router.label = label
  1253         1          1.0      1.0      0.0          return cb_router

Total time: 0.275631 s
Function: create at line 1341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1341                                               @dispatch(event="provider.networking.floating_ips.create",
  1342                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1343                                               @profile
  1344                                               def create(self, gateway):
  1345         1         12.0     12.0      0.0          log.debug("Creating a floating IP under gateway %s", gateway)
  1346         1         10.0     10.0      0.0          ip = self.provider.ec2_conn.meta.client.allocate_address(
  1347         1     274365.0 274365.0     99.5              Domain='vpc')
  1348         1          3.0      3.0      0.0          return AWSFloatingIP(
  1349         1          3.0      3.0      0.0              self.provider,
  1350         1       1238.0   1238.0      0.4              self.provider.ec2_conn.VpcAddress(ip.get('AllocationId')))

Total time: 0.274904 s
Function: label at line 640

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   640                                               @label.setter
   641                                               # pylint:disable=arguments-differ
   642                                               @profile
   643                                               def label(self, value):
   644         2         18.0      9.0      0.0          self.assert_valid_resource_label(value)
   645         2          2.0      1.0      0.0          self._vm_firewall.create_tags(Tags=[{'Key': 'Name',
   646         2     274884.0 137442.0    100.0                                               'Value': value or ""}])

Total time: 0.26292 s
Function: refresh at line 930

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   930                                               @profile
   931                                               def refresh(self):
   932         1          2.0      2.0      0.0          try:
   933         1     262913.0 262913.0    100.0              self._vpc.reload()
   934         1          5.0      5.0      0.0              self._unknown_state = False
   935                                                   except ClientError:
   936                                                       # The network no longer exists and cannot be refreshed.
   937                                                       # set the status to unknown
   938                                                       self._unknown_state = True

Total time: 0.257867 s
Function: description at line 655

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   655                                               @description.setter
   656                                               # pylint:disable=arguments-differ
   657                                               @profile
   658                                               def description(self, value):
   659         2          3.0      1.5      0.0          self._vm_firewall.create_tags(Tags=[{'Key': 'Description',
   660         2     257864.0 128932.0    100.0                                               'Value': value or ""}])

Total time: 0.257728 s
Function: get at line 633

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   633                                               @profile
   634                                               def get(self, image_id):
   635         2         13.0      6.5      0.0          log.debug("Getting AWS Image Service with the id: %s", image_id)
   636         2     257715.0 128857.5    100.0          return self.svc.get(image_id)

Total time: 0.24604 s
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
   395         1     246037.0 246037.0    100.0              volume._volume.delete()

Total time: 0.24311 s
Function: find at line 822

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   822                                               @dispatch(event="provider.compute.instances.find",
   823                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   824                                               @profile
   825                                               def find(self, **kwargs):
   826         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
   827                                           
   828                                                   # All kwargs should have been popped at this time.
   829         3          5.0      1.7      0.0          if len(kwargs) > 0:
   830         1          0.0      0.0      0.0              raise InvalidParamException(
   831         1          0.0      0.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   832         1         12.0     12.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   833                                           
   834         2     243087.0 121543.5    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.217225 s
Function: list at line 1049

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1049                                               @dispatch(event="provider.networking.subnets.list",
  1050                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1051                                               @profile
  1052                                               def list(self, network=None, limit=None, marker=None):
  1053         1         18.0     18.0      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1054         1          2.0      2.0      0.0          if network_id:
  1055         1          7.0      7.0      0.0              return self.svc.find(
  1056         1          1.0      1.0      0.0                  filter_name='vpc-id', filter_value=network_id,
  1057         1     217197.0 217197.0    100.0                  limit=limit, marker=marker)
  1058                                                   else:
  1059                                                       return self.svc.list(limit=limit, marker=marker)

Total time: 0.212642 s
Function: create at line 134

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   134                                               @dispatch(event="provider.security.key_pairs.create",
   135                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   136                                               @profile
   137                                               def create(self, name, public_key_material=None):
   138         1          9.0      9.0      0.0          AWSKeyPair.assert_valid_resource_name(name)
   139         1          1.0      1.0      0.0          private_key = None
   140         1          1.0      1.0      0.0          if not public_key_material:
   141         1      76661.0  76661.0     36.1              public_key_material, private_key = cb_helpers.generate_key_pair()
   142         1          2.0      2.0      0.0          try:
   143         1          3.0      3.0      0.0              kp = self.svc.create('import_key_pair', KeyName=name,
   144         1     135961.0 135961.0     63.9                                   PublicKeyMaterial=public_key_material)
   145         1          4.0      4.0      0.0              kp.material = private_key
   146         1          0.0      0.0      0.0              return kp
   147                                                   except ClientError as e:
   148                                                       if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
   149                                                           raise DuplicateResourceException(
   150                                                               'Keypair already exists with name {0}'.format(name))
   151                                                       else:
   152                                                           raise e

Total time: 0.186605 s
Function: refresh at line 593

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   593                                               @profile
   594                                               def refresh(self):
   595         2          6.0      3.0      0.0          try:
   596         2     186595.0  93297.5    100.0              self._snapshot.reload()
   597         2          4.0      2.0      0.0              self._unknown_state = False
   598                                                   except ClientError:
   599                                                       # The snapshot no longer exists and cannot be refreshed.
   600                                                       # set the status to unknown
   601                                                       self._unknown_state = True

Total time: 0.18114 s
Function: label at line 975

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   975                                               @label.setter
   976                                               # pylint:disable=arguments-differ
   977                                               @profile
   978                                               def label(self, value):
   979         1          7.0      7.0      0.0          self.assert_valid_resource_label(value)
   980         1     181133.0 181133.0    100.0          self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.172383 s
Function: delete at line 1255

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1255                                               @dispatch(event="provider.networking.routers.delete",
  1256                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1257                                               @profile
  1258                                               def delete(self, router):
  1259         1          3.0      3.0      0.0          r = router if isinstance(router, AWSRouter) else self.get(router)
  1260         1          1.0      1.0      0.0          if r:
  1261                                                       # pylint:disable=protected-access
  1262         1     172379.0 172379.0    100.0              r._route_table.delete()

Total time: 0.167096 s
Function: refresh at line 1069

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1069                                               @profile
  1070                                               def refresh(self):
  1071         2          3.0      1.5      0.0          try:
  1072         2     167093.0  83546.5    100.0              self._route_table.reload()
  1073                                                   except ClientError:
  1074                                                       self._route_table.associations = None

Total time: 0.155392 s
Function: label at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @label.setter
   897                                               # pylint:disable=arguments-differ
   898                                               @profile
   899                                               def label(self, value):
   900         1          9.0      9.0      0.0          self.assert_valid_resource_label(value)
   901         1     155383.0 155383.0    100.0          self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.142324 s
Function: label at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @label.setter
  1062                                               # pylint:disable=arguments-differ
  1063                                               @profile
  1064                                               def label(self, value):
  1065         1         11.0     11.0      0.0          self.assert_valid_resource_label(value)
  1066         1          1.0      1.0      0.0          self._route_table.create_tags(Tags=[{'Key': 'Name',
  1067         1     142312.0 142312.0    100.0                                               'Value': value or ""}])

Total time: 0.137572 s
Function: delete at line 154

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   154                                               @dispatch(event="provider.security.key_pairs.delete",
   155                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   156                                               @profile
   157                                               def delete(self, key_pair):
   158         1          3.0      3.0      0.0          key_pair = (key_pair if isinstance(key_pair, AWSKeyPair) else
   159                                                               self.get(key_pair))
   160         1          1.0      1.0      0.0          if key_pair:
   161                                                       # pylint:disable=protected-access
   162         1     137568.0 137568.0    100.0              key_pair._key_pair.delete()

Total time: 0.130891 s
Function: list at line 232

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   232                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   233                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   234                                               @profile
   235                                               def list(self, firewall, limit=None, marker=None):
   236                                                   # pylint:disable=protected-access
   237        12         19.0      1.6      0.0          rules = [AWSVMFirewallRule(firewall,
   238                                                                              TrafficDirection.INBOUND, r)
   239        12     129948.0  10829.0     99.3                   for r in firewall._vm_firewall.ip_permissions]
   240                                                   # pylint:disable=protected-access
   241        12         14.0      1.2      0.0          rules = rules + [
   242        12         17.0      1.4      0.0              AWSVMFirewallRule(
   243                                                           firewall, TrafficDirection.OUTBOUND, r)
   244        12        527.0     43.9      0.4              for r in firewall._vm_firewall.ip_permissions_egress]
   245        12         34.0      2.8      0.0          return ClientPagedResultList(self.provider, rules,
   246        12        332.0     27.7      0.3                                       limit=limit, marker=marker)

Total time: 0.12099 s
Function: delete at line 452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   452                                               @dispatch(event="provider.storage.snapshots.delete",
   453                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   454                                               @profile
   455                                               def delete(self, snapshot):
   456         1          2.0      2.0      0.0          snapshot = (snapshot if isinstance(snapshot, AWSSnapshot) else
   457                                                               self.get(snapshot))
   458         1          0.0      0.0      0.0          if snapshot:
   459                                                       # pylint:disable=protected-access
   460         1     120988.0 120988.0    100.0              snapshot._snapshot.delete()

Total time: 0.119243 s
Function: delete at line 1295

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1295                                               @dispatch(event="provider.networking.gateways.delete",
  1296                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1297                                               @profile
  1298                                               def delete(self, network, gateway):
  1299         1          2.0      2.0      0.0          gw = (gateway if isinstance(gateway, AWSInternetGateway)
  1300                                                         else self.svc.get(gateway))
  1301         1          1.0      1.0      0.0          try:
  1302         1          8.0      8.0      0.0              if gw.network_id:
  1303                                                           # pylint:disable=protected-access
  1304                                                           gw._gateway.detach_from_vpc(VpcId=gw.network_id)
  1305                                                   except ClientError as e:
  1306                                                       log.warn("Error deleting gateway {0}: {1}".format(self.id, e))
  1307                                                   # pylint:disable=protected-access
  1308         1     119232.0 119232.0    100.0          gw._gateway.delete()

Total time: 0.10803 s
Function: label at line 426

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   426                                               @label.setter
   427                                               # pylint:disable=arguments-differ
   428                                               @profile
   429                                               def label(self, value):
   430         1          9.0      9.0      0.0          self.assert_valid_resource_label(value)
   431         1     108021.0 108021.0    100.0          self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.084704 s
Function: get at line 963

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   963                                               @dispatch(event="provider.networking.networks.get",
   964                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   965                                               @profile
   966                                               def get(self, network_id):
   967         1      84704.0  84704.0    100.0          return self.svc.get(network_id)

Total time: 0.084315 s
Function: get at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @dispatch(event="provider.compute.regions.get",
   897                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   898                                               @profile
   899                                               def get(self, region_id):
   900         1          2.0      2.0      0.0          log.debug("Getting AWS Region Service with the id: %s",
   901         1          6.0      6.0      0.0                    region_id)
   902         1      84307.0  84307.0    100.0          region = [r for r in self if r.id == region_id]
   903         1          0.0      0.0      0.0          if region:
   904         1          0.0      0.0      0.0              return region[0]
   905                                                   else:
   906                                                       return None

Total time: 0.073234 s
Function: list at line 908

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   908                                               @dispatch(event="provider.compute.regions.list",
   909                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   910                                               @profile
   911                                               def list(self, limit=None, marker=None):
   912                                                   regions = [
   913         1         20.0     20.0      0.0              AWSRegion(self.provider, region) for region in
   914         1      73133.0  73133.0     99.9              self.provider.ec2_conn.meta.client.describe_regions()
   915         1         52.0     52.0      0.1              .get('Regions', [])]
   916         1          2.0      2.0      0.0          return ClientPagedResultList(self.provider, regions,
   917         1         27.0     27.0      0.0                                       limit=limit, marker=marker)

Total time: 2.1e-05 s
Function: create_launch_config at line 765

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   765                                               @profile
   766                                               def create_launch_config(self):
   767         2         21.0     10.5    100.0          return AWSLaunchConfig(self.provider)

