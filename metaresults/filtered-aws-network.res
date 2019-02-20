cloudbridge.test.test_network_service.CloudNetworkServiceTestCase


Test output
 ........
----------------------------------------------------------------------
Ran 8 tests in 30.995s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 3.05072 s
Function: create at line 990

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   990                                               @dispatch(event="provider.networking.networks.create",
   991                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   992                                               @profile
   993                                               def create(self, label, cidr_block):
   994        14        195.0     13.9      0.0          AWSNetwork.assert_valid_resource_label(label)
   995                                           
   996         4    1045892.0 261473.0     34.3          cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
   997                                                   # Wait until ready to tag instance
   998         4    1455860.0 363965.0     47.7          cb_net.wait_till_ready()
   999         4          2.0      0.5      0.0          if label:
  1000         4     548765.0 137191.2     18.0              cb_net.label = label
  1001         4          4.0      1.0      0.0          return cb_net

Total time: 1.91408 s
Function: list at line 1049

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1049                                               @dispatch(event="provider.networking.subnets.list",
  1050                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1051                                               @profile
  1052                                               def list(self, network=None, limit=None, marker=None):
  1053        14         67.0      4.8      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1054        14         14.0      1.0      0.0          if network_id:
  1055         6         16.0      2.7      0.0              return self.svc.find(
  1056         6          2.0      0.3      0.0                  filter_name='vpc-id', filter_value=network_id,
  1057         6     806283.0 134380.5     42.1                  limit=limit, marker=marker)
  1058                                                   else:
  1059         8    1107701.0 138462.6     57.9              return self.svc.list(limit=limit, marker=marker)

Total time: 1.73717 s
Function: get_or_create at line 1273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1273                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1274                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1275                                               @profile
  1276                                               def get_or_create(self, network):
  1277         3          6.0      2.0      0.0          network_id = network.id if isinstance(
  1278         3         30.0     10.0      0.0              network, AWSNetwork) else network
  1279                                                   # Don't filter by label because it may conflict with at least the
  1280                                                   # default VPC that most accounts have but that network is typically
  1281                                                   # without a name.
  1282         3          8.0      2.7      0.0          gtw = self.svc.find(filter_name='attachment.vpc-id',
  1283         3     422247.0 140749.0     24.3                              filter_value=network_id)
  1284         3          6.0      2.0      0.0          if gtw:
  1285                                                       return gtw[0]  # There can be only one gtw attached to a VPC
  1286                                                   # Gateway does not exist so create one and attach to the supplied net
  1287         3     406758.0 135586.0     23.4          cb_gateway = self.svc.create('create_internet_gateway')
  1288         3          6.0      2.0      0.0          cb_gateway._gateway.create_tags(
  1289         3          3.0      1.0      0.0              Tags=[{'Key': 'Name',
  1290         3     511906.0 170635.3     29.5                     'Value': AWSInternetGateway.CB_DEFAULT_INET_GATEWAY_NAME
  1291                                                              }])
  1292         3     396197.0 132065.7     22.8          cb_gateway._gateway.attach_to_vpc(VpcId=network_id)
  1293         3          5.0      1.7      0.0          return cb_gateway

Total time: 1.50173 s
Function: list at line 1335

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1335                                               @dispatch(event="provider.networking.floating_ips.list",
  1336                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1337                                               @profile
  1338                                               def list(self, gateway, limit=None, marker=None):
  1339        10    1501728.0 150172.8    100.0          return self.svc.list(limit, marker)

Total time: 1.45562 s
Function: list at line 1238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1238                                               @dispatch(event="provider.networking.routers.list",
  1239                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1240                                               @profile
  1241                                               def list(self, limit=None, marker=None):
  1242        22    1455619.0  66164.5    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 1.21929 s
Function: delete at line 1003

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1003                                               @dispatch(event="provider.networking.networks.delete",
  1004                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1005                                               @profile
  1006                                               def delete(self, network):
  1007         4         10.0      2.5      0.0          network = (network if isinstance(network, AWSNetwork)
  1008                                                              else self.get(network))
  1009         4          3.0      0.8      0.0          if network:
  1010                                                       # pylint:disable=protected-access
  1011         4    1219278.0 304819.5    100.0              network._vpc.delete()

Total time: 1.21166 s
Function: create at line 1076

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1076                                               @dispatch(event="provider.networking.subnets.create",
  1077                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1078                                               @profile
  1079                                               def create(self, label, network, cidr_block, zone):
  1080        13        222.0     17.1      0.0          AWSSubnet.assert_valid_resource_label(label)
  1081         3          3.0      1.0      0.0          zone_name = zone.name if isinstance(
  1082         3          6.0      2.0      0.0              zone, AWSPlacementZone) else zone
  1083                                           
  1084         3         24.0      8.0      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1085                                           
  1086         3         11.0      3.7      0.0          subnet = self.svc.create('create_subnet',
  1087         3          2.0      0.7      0.0                                   VpcId=network_id,
  1088         3          2.0      0.7      0.0                                   CidrBlock=cidr_block,
  1089         3     695845.0 231948.3     57.4                                   AvailabilityZone=zone_name)
  1090         3          7.0      2.3      0.0          if label:
  1091         3     515534.0 171844.7     42.5              subnet.label = label
  1092         3          4.0      1.3      0.0          return subnet

Total time: 1.15518 s
Function: list at line 969

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   969                                               @dispatch(event="provider.networking.networks.list",
   970                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   971                                               @profile
   972                                               def list(self, limit=None, marker=None):
   973         8    1155181.0 144397.6    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 1.07916 s
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065         6         12.0      2.0      0.0          label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068         6          5.0      0.8      0.0          if len(kwargs) > 0:
  1069         1          0.0      0.0      0.0              raise InvalidParamException(
  1070         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1071         1         10.0     10.0      0.0                  "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073         5         49.0      9.8      0.0          log.debug("Searching for AWS Subnet Service %s", label)
  1074         5    1079080.0 215816.0    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 1.00426 s
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105         3         12.0      4.0      0.0          zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
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
  1130         3    1004144.0 334714.7    100.0          snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132         3          5.0      1.7      0.0          if snl:
  1133                                                       # pylint:disable=protected-access
  1134         3         37.0     12.3      0.0              snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135         3          3.0      1.0      0.0              if not zone_name:
  1136                                                           return snl[0]
  1137         3          3.0      1.0      0.0              for subnet in snl:
  1138         3         54.0     18.0      0.0                  if subnet.zone.name == zone_name:
  1139         3          3.0      1.0      0.0                      return subnet
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

Total time: 0.932473 s
Function: find at line 1223

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1223                                               @dispatch(event="provider.networking.routers.find",
  1224                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1225                                               @profile
  1226                                               def find(self, **kwargs):
  1227         3          7.0      2.3      0.0          label = kwargs.pop('label', None)
  1228                                           
  1229                                                   # All kwargs should have been popped at this time.
  1230         3          5.0      1.7      0.0          if len(kwargs) > 0:
  1231         1          0.0      0.0      0.0              raise InvalidParamException(
  1232         1          0.0      0.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1233         1         14.0     14.0      0.0                  "attributes: %s" % (kwargs, 'label'))
  1234                                           
  1235         2         13.0      6.5      0.0          log.debug("Searching for AWS Router Service %s", label)
  1236         2     932434.0 466217.0    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.887973 s
Function: delete at line 1352

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1352                                               @dispatch(event="provider.networking.floating_ips.delete",
  1353                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1354                                               @profile
  1355                                               def delete(self, gateway, fip):
  1356         2          5.0      2.5      0.0          if isinstance(fip, AWSFloatingIP):
  1357                                                       # pylint:disable=protected-access
  1358                                                       aws_fip = fip._ip
  1359                                                   else:
  1360         2     524012.0 262006.0     59.0              aws_fip = self.svc.get_raw(fip)
  1361         2     363956.0 181978.0     41.0          aws_fip.release()

Total time: 0.855001 s
Function: get at line 963

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   963                                               @dispatch(event="provider.networking.networks.get",
   964                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   965                                               @profile
   966                                               def get(self, network_id):
   967         8     855001.0 106875.1    100.0          return self.svc.get(network_id)

Total time: 0.854453 s
Function: label at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @label.setter
   897                                               # pylint:disable=arguments-differ
   898                                               @profile
   899                                               def label(self, value):
   900        15        164.0     10.9      0.0          self.assert_valid_resource_label(value)
   901         7     854289.0 122041.3    100.0          self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.846852 s
Function: label at line 975

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   975                                               @label.setter
   976                                               # pylint:disable=arguments-differ
   977                                               @profile
   978                                               def label(self, value):
   979        14        157.0     11.2      0.0          self.assert_valid_resource_label(value)
   980         6     846695.0 141115.8    100.0          self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0.710526 s
Function: delete at line 1094

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1094                                               @dispatch(event="provider.networking.subnets.delete",
  1095                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1096                                               @profile
  1097                                               def delete(self, subnet):
  1098         3          6.0      2.0      0.0          sn = subnet if isinstance(subnet, AWSSubnet) else self.get(subnet)
  1099         3          3.0      1.0      0.0          if sn:
  1100                                                       # pylint:disable=protected-access
  1101         3     710517.0 236839.0    100.0              sn._subnet.delete()

Total time: 0.70085 s
Function: delete at line 1295

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1295                                               @dispatch(event="provider.networking.gateways.delete",
  1296                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1297                                               @profile
  1298                                               def delete(self, network, gateway):
  1299         3          8.0      2.7      0.0          gw = (gateway if isinstance(gateway, AWSInternetGateway)
  1300                                                         else self.svc.get(gateway))
  1301         3          4.0      1.3      0.0          try:
  1302         3         46.0     15.3      0.0              if gw.network_id:
  1303                                                           # pylint:disable=protected-access
  1304         2     292032.0 146016.0     41.7                  gw._gateway.detach_from_vpc(VpcId=gw.network_id)
  1305                                                   except ClientError as e:
  1306                                                       log.warn("Error deleting gateway {0}: {1}".format(self.id, e))
  1307                                                   # pylint:disable=protected-access
  1308         3     408760.0 136253.3     58.3          gw._gateway.delete()

Total time: 0.537054 s
Function: refresh at line 930

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   930                                               @profile
   931                                               def refresh(self):
   932         7         11.0      1.6      0.0          try:
   933         7     537026.0  76718.0    100.0              self._vpc.reload()
   934         7         17.0      2.4      0.0              self._unknown_state = False
   935                                                   except ClientError:
   936                                                       # The network no longer exists and cannot be refreshed.
   937                                                       # set the status to unknown
   938                                                       self._unknown_state = True

Total time: 0.50429 s
Function: create at line 1341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1341                                               @dispatch(event="provider.networking.floating_ips.create",
  1342                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1343                                               @profile
  1344                                               def create(self, gateway):
  1345         2         20.0     10.0      0.0          log.debug("Creating a floating IP under gateway %s", gateway)
  1346         2         20.0     10.0      0.0          ip = self.provider.ec2_conn.meta.client.allocate_address(
  1347         2     501672.0 250836.0     99.5              Domain='vpc')
  1348         2          5.0      2.5      0.0          return AWSFloatingIP(
  1349         2          7.0      3.5      0.0              self.provider,
  1350         2       2566.0   1283.0      0.5              self.provider.ec2_conn.VpcAddress(ip.get('AllocationId')))

Total time: 0.500526 s
Function: label at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @label.setter
  1062                                               # pylint:disable=arguments-differ
  1063                                               @profile
  1064                                               def label(self, value):
  1065        12        158.0     13.2      0.0          self.assert_valid_resource_label(value)
  1066         4          5.0      1.2      0.0          self._route_table.create_tags(Tags=[{'Key': 'Name',
  1067         4     500363.0 125090.8    100.0                                               'Value': value or ""}])

Total time: 0.442382 s
Function: find at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.networking.floating_ips.find",
   376                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def find(self, gateway, **kwargs):
   379         3         12.0      4.0      0.0          obj_list = gateway.floating_ips
   380         3          2.0      0.7      0.0          filters = ['name', 'public_ip']
   381         3     442312.0 147437.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   382         2         56.0     28.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.276254 s
Function: create at line 1244

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1244                                               @dispatch(event="provider.networking.routers.create",
  1245                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1246                                               @profile
  1247                                               def create(self, label, network):
  1248         1          7.0      7.0      0.0          network_id = network.id if isinstance(network, AWSNetwork) else network
  1249                                           
  1250         1     131667.0 131667.0     47.7          cb_router = self.svc.create('create_route_table', VpcId=network_id)
  1251         1          1.0      1.0      0.0          if label:
  1252         1     144578.0 144578.0     52.3              cb_router.label = label
  1253         1          1.0      1.0      0.0          return cb_router

Total time: 0.247562 s
Function: refresh at line 1069

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1069                                               @profile
  1070                                               def refresh(self):
  1071         3          4.0      1.3      0.0          try:
  1072         3     247558.0  82519.3    100.0              self._route_table.reload()
  1073                                                   except ClientError:
  1074                                                       self._route_table.associations = None

Total time: 0.177915 s
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
  1262         1     177911.0 177911.0    100.0              r._route_table.delete()

Total time: 0.175809 s
Function: get at line 1043

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1043                                               @dispatch(event="provider.networking.subnets.get",
  1044                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1045                                               @profile
  1046                                               def get(self, subnet_id):
  1047         2     175809.0  87904.5    100.0          return self.svc.get(subnet_id)

Total time: 0.164269 s
Function: find at line 975

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   975                                               @dispatch(event="provider.networking.networks.find",
   976                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   977                                               @profile
   978                                               def find(self, **kwargs):
   979         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
   980                                           
   981                                                   # All kwargs should have been popped at this time.
   982         3          4.0      1.3      0.0          if len(kwargs) > 0:
   983         1          0.0      0.0      0.0              raise InvalidParamException(
   984         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   985         1          9.0      9.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   986                                           
   987         2         13.0      6.5      0.0          log.debug("Searching for AWS Network Service %s", label)
   988         2     164236.0  82118.0    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0.13601 s
Function: get at line 1328

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1328                                               @dispatch(event="provider.networking.floating_ips.get",
  1329                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1330                                               @profile
  1331                                               def get(self, gateway, fip_id):
  1332         2         12.0      6.0      0.0          log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
  1333         2     135998.0  67999.0    100.0          return self.svc.get(fip_id)

Total time: 0.109509 s
Function: get at line 1217

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1217                                               @dispatch(event="provider.networking.routers.get",
  1218                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1219                                               @profile
  1220                                               def get(self, router_id):
  1221         2     109509.0  54754.5    100.0          return self.svc.get(router_id)

Total time: 0.068226 s
Function: refresh at line 1006

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1006                                               @profile
  1007                                               def refresh(self):
  1008         1          1.0      1.0      0.0          try:
  1009         1      68223.0  68223.0    100.0              self._subnet.reload()
  1010         1          2.0      2.0      0.0              self._unknown_state = False
  1011                                                   except ClientError:
  1012                                                       # subnet no longer exists
  1013                                                       self._unknown_state = True

