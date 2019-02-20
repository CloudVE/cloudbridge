cloudbridge.test.test_image_service.CloudImageServiceTestCase


Test output
 ..
----------------------------------------------------------------------
Ran 2 tests in 110.730s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 9.5028 s
Function: refresh at line 376

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   376                                               @profile
   377                                               def refresh(self):
   378        65        304.0      4.7      0.0          try:
   379        65    9502299.0 146189.2    100.0              self._ec2_instance.reload()
   380        65        201.0      3.1      0.0              self._unknown_state = False
   381                                                   except ClientError:
   382                                                       # The instance no longer exists and cannot be refreshed.
   383                                                       # set the state to unknown
   384                                                       self._unknown_state = True

Total time: 4.28092 s
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
   776         2         10.0      5.0      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   777                                                   vm_size = vm_type.id if \
   778         2          2.0      1.0      0.0              isinstance(vm_type, VMType) else vm_type
   779                                                   subnet = (self.provider.networking.subnets.get(subnet)
   780         2          4.0      2.0      0.0                    if isinstance(subnet, str) else subnet)
   781         2          4.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   782         2          0.0      0.0      0.0          key_pair_name = key_pair.name if isinstance(
   783         2          1.0      0.5      0.0              key_pair,
   784         2          4.0      2.0      0.0              KeyPair) else key_pair
   785         2          1.0      0.5      0.0          if launch_config:
   786                                                       bdm = self._process_block_device_mappings(launch_config)
   787                                                   else:
   788         2          1.0      0.5      0.0              bdm = None
   789                                           
   790                                                   subnet_id, zone_id, vm_firewall_ids = \
   791         2         54.0     27.0      0.0              self._resolve_launch_options(subnet, zone_id, vm_firewalls)
   792                                           
   793         2          2.0      1.0      0.0          placement = {'AvailabilityZone': zone_id} if zone_id else None
   794         2          5.0      2.5      0.0          inst = self.svc.create('create_instances',
   795         2          2.0      1.0      0.0                                 ImageId=image_id,
   796         2          0.0      0.0      0.0                                 MinCount=1,
   797         2          2.0      1.0      0.0                                 MaxCount=1,
   798         2          2.0      1.0      0.0                                 KeyName=key_pair_name,
   799         2          2.0      1.0      0.0                                 SecurityGroupIds=vm_firewall_ids or None,
   800         2          4.0      2.0      0.0                                 UserData=str(user_data) or None,
   801         2          1.0      0.5      0.0                                 InstanceType=vm_size,
   802         2          1.0      0.5      0.0                                 Placement=placement,
   803         2          2.0      1.0      0.0                                 BlockDeviceMappings=bdm,
   804         2    3397811.0 1698905.5     79.4                                 SubnetId=subnet_id
   805                                                                          )
   806         2          6.0      3.0      0.0          if inst and len(inst) == 1:
   807                                                       # Wait until the resource exists
   808                                                       # pylint:disable=protected-access
   809         2     446604.0 223302.0     10.4              inst[0]._wait_till_exists()
   810                                                       # Tag the instance w/ the name
   811         2     436371.0 218185.5     10.2              inst[0].label = label
   812         2          4.0      2.0      0.0              return inst[0]
   813                                                   raise ValueError(
   814                                                       'Expected a single object response, got a list: %s' % inst)

Total time: 2.65148 s
Function: find at line 638

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   638                                               @profile
   639                                               def find(self, **kwargs):
   640                                                   # Filter by name or label
   641         3          5.0      1.7      0.0          label = kwargs.pop('label', None)
   642                                                   # Popped here, not used in the generic find
   643         3          3.0      1.0      0.0          owner = kwargs.pop('owners', None)
   644                                           
   645                                                   # All kwargs should have been popped at this time.
   646         3          3.0      1.0      0.0          if len(kwargs) > 0:
   647         1          1.0      1.0      0.0              raise InvalidParamException(
   648         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   649         1         11.0     11.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   650                                           
   651         2          0.0      0.0      0.0          extra_args = {}
   652         2          2.0      1.0      0.0          if owner:
   653         1          1.0      1.0      0.0              extra_args.update(Owners=owner)
   654                                           
   655                                                   # The original list is made by combining both searches by "tag:Name"
   656                                                   # and "AMI name" to allow for searches of public images
   657         2          1.0      0.5      0.0          if label:
   658         2         13.0      6.5      0.0              log.debug("Searching for AWS Image Service %s", label)
   659         2          1.0      0.5      0.0              obj_list = []
   660         2          3.0      1.5      0.0              obj_list.extend(self.svc.find(filter_name='name',
   661         2    1225611.0 612805.5     46.2                                            filter_value=label, **extra_args))
   662         2          5.0      2.5      0.0              obj_list.extend(self.svc.find(filter_name='tag:Name',
   663         2    1425801.0 712900.5     53.8                                            filter_value=label, **extra_args))
   664         2         22.0     11.0      0.0              return obj_list
   665                                                   else:
   666                                                       return []

Total time: 2.61199 s
Function: refresh at line 134

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   134                                               @profile
   135                                               def refresh(self):
   136        22    2611990.0 118726.8    100.0          self._ec2_image.reload()

Total time: 0.584476 s
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
   460         1     584474.0 584474.0    100.0              snapshot._snapshot.delete()

Total time: 0.565674 s
Function: list at line 668

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   668                                               @profile
   669                                               def list(self, filter_by_owner=True, limit=None, marker=None):
   670         5         16.0      3.2      0.0          return self.svc.list(Owners=['self'] if filter_by_owner else
   671                                                                        ['amazon', 'self'],
   672         5     565658.0 113131.6    100.0                               limit=limit, marker=marker)

Total time: 0.541265 s
Function: label at line 88

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    88                                               @label.setter
    89                                               # pylint:disable=arguments-differ
    90                                               @profile
    91                                               def label(self, value):
    92        12        162.0     13.5      0.0          self.assert_valid_resource_label(value)
    93         4          6.0      1.5      0.0          self._ec2_image.create_tags(Tags=[{'Key': 'Name',
    94         4     541097.0 135274.2    100.0                                             'Value': value or ""}])

Total time: 0.436325 s
Function: label at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @label.setter
   255                                               # pylint:disable=arguments-differ
   256                                               @profile
   257                                               def label(self, value):
   258         2         24.0     12.0      0.0          self.assert_valid_resource_label(value)
   259         2          8.0      4.0      0.0          self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
   260         2     436293.0 218146.5    100.0                                                'Value': value or ""}])

Total time: 0.353906 s
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
   850         2     353900.0 176950.0    100.0              aws_inst._ec2_instance.terminate()

Total time: 0.284701 s
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105         1          6.0      6.0      0.0          zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
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
  1130         1     284614.0 284614.0    100.0          snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132         1          2.0      2.0      0.0          if snl:
  1133                                                       # pylint:disable=protected-access
  1134         1         49.0     49.0      0.0              snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135         1          2.0      2.0      0.0              if not zone_name:
  1136                                                           return snl[0]
  1137         1          1.0      1.0      0.0              for subnet in snl:
  1138         1         26.0     26.0      0.0                  if subnet.zone.name == zone_name:
  1139         1          1.0      1.0      0.0                      return subnet
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

Total time: 0.243766 s
Function: get at line 633

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   633                                               @profile
   634                                               def get(self, image_id):
   635         2         12.0      6.0      0.0          log.debug("Getting AWS Image Service with the id: %s", image_id)
   636         2     243754.0 121877.0    100.0          return self.svc.get(image_id)

Total time: 0.225429 s
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065         1          2.0      2.0      0.0          label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068         1          1.0      1.0      0.0          if len(kwargs) > 0:
  1069                                                       raise InvalidParamException(
  1070                                                           "Unrecognised parameters for search: %s. Supported "
  1071                                                           "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073         1         20.0     20.0      0.0          log.debug("Searching for AWS Subnet Service %s", label)
  1074         1     225406.0 225406.0    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.094928 s
Function: get at line 406

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   406                                               @dispatch(event="provider.storage.snapshots.get",
   407                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   408                                               @profile
   409                                               def get(self, snapshot_id):
   410         1      94928.0  94928.0    100.0          return self.svc.get(snapshot_id)

