cloudbridge.test.test_network_service.CloudNetworkServiceTestCase


Test output
 ........
----------------------------------------------------------------------
Ran 8 tests in 112.996s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 19.2371 s
Function: get_or_create at line 1249

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1249                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1250                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1251                                               @profile
  1252                                               def get_or_create(self, network):
  1253                                                   """For OS, inet gtw is any net that has `external` property set."""
  1254         3         22.0      7.3      0.0          external_nets = (n for n in self._provider.networking.networks
  1255                                                                    if n.external)
  1256         3    1216733.0 405577.7      6.3          for net in external_nets:
  1257         3   18020271.0 6006757.0     93.7              if self._check_fip_connectivity(network, net):
  1258         3         86.0     28.7      0.0                  return OpenStackInternetGateway(self._provider, net)
  1259                                                   return None

Total time: 17.2713 s
Function: list at line 1042

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1042                                               @dispatch(event="provider.networking.networks.list",
  1043                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1044                                               @profile
  1045                                               def list(self, limit=None, marker=None):
  1046        43         65.0      1.5      0.0          networks = [OpenStackNetwork(self.provider, network)
  1047        43   17266287.0 401541.6    100.0                      for network in self.provider.neutron.list_networks()
  1048        43       3104.0     72.2      0.0                      .get('networks') if network]
  1049        43         89.0      2.1      0.0          return ClientPagedResultList(self.provider, networks,
  1050        43       1733.0     40.3      0.0                                       limit=limit, marker=marker)

Total time: 14.0636 s
Function: get at line 1035

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1035                                               @dispatch(event="provider.networking.networks.get",
  1036                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1037                                               @profile
  1038                                               def get(self, network_id):
  1039        35        103.0      2.9      0.0          network = (n for n in self if n.id == network_id)
  1040        35   14063482.0 401813.8    100.0          return next(network, None)

Total time: 14.0561 s
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122        30         49.0      1.6      0.0          if network:
  1123         6         29.0      4.8      0.0              network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125         6        312.0     52.0      0.0              subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128        24         35.0      1.5      0.0              subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129        24   14054354.0 585598.1    100.0                         self.provider.neutron.list_subnets().get('subnets', [])]
  1130        30        107.0      3.6      0.0          return ClientPagedResultList(self.provider, subnets,
  1131        30       1249.0     41.6      0.0                                       limit=limit, marker=marker)

Total time: 13.9178 s
Function: create at line 1071

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1071                                               @dispatch(event="provider.networking.networks.create",
  1072                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1073                                               @profile
  1074                                               def create(self, label, cidr_block):
  1075        14        177.0     12.6      0.0          OpenStackNetwork.assert_valid_resource_label(label)
  1076         4          4.0      1.0      0.0          net_info = {'name': label or ""}
  1077         4    9277143.0 2319285.8     66.7          network = self.provider.neutron.create_network({'network': net_info})
  1078         4        161.0     40.2      0.0          cb_net = OpenStackNetwork(self.provider, network.get('network'))
  1079         4          5.0      1.2      0.0          if label:
  1080         4    4640334.0 1160083.5     33.3              cb_net.label = label
  1081         4          4.0      1.0      0.0          return cb_net

Total time: 10.9466 s
Function: refresh at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @profile
   843                                               def refresh(self):
   844                                                   """Refresh the state of this network by re-querying the provider."""
   845        27   10946477.0 405425.1    100.0          network = self._provider.networking.networks.get(self.id)
   846        27         32.0      1.2      0.0          if network:
   847                                                       # pylint:disable=protected-access
   848        15         22.0      1.5      0.0              self._network = network._network
   849                                                   else:
   850                                                       # Network no longer exists
   851        12         24.0      2.0      0.0              self._network = {}

Total time: 8.22129 s
Function: label at line 811

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   811                                               @label.setter
   812                                               @profile
   813                                               def label(self, value):
   814                                                   """
   815                                                   Set the network label.
   816                                                   """
   817        15        184.0     12.3      0.0          self.assert_valid_resource_label(value)
   818         7         53.0      7.6      0.0          self._provider.neutron.update_network(
   819         7    5363809.0 766258.4     65.2              self.id, {'network': {'name': value or ""}})
   820         7    2857243.0 408177.6     34.8          self.refresh()

Total time: 7.86342 s
Function: delete at line 1219

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1219                                               @dispatch(event="provider.networking.routers.delete",
  1220                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1221                                               @profile
  1222                                               def delete(self, router):
  1223         4         57.0     14.2      0.0          r_id = router.id if isinstance(router, OpenStackRouter) else router
  1224         4    7863364.0 1965841.0    100.0          self.provider.os_conn.delete_router(r_id)

Total time: 6.85171 s
Function: delete at line 1083

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1083                                               @dispatch(event="provider.networking.networks.delete",
  1084                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1085                                               @profile
  1086                                               def delete(self, network):
  1087         4          9.0      2.2      0.0          network = (network if isinstance(network, OpenStackNetwork) else
  1088                                                              self.get(network))
  1089         4          8.0      2.0      0.0          if not network:
  1090                                                       return
  1091         4         19.0      4.8      0.0          if not network.external and network.id in str(
  1092         4    1530910.0 382727.5     22.3                  self.provider.neutron.list_networks()):
  1093                                                       # If there are ports associated with the network, it won't delete
  1094         4         43.0     10.8      0.0              ports = self.provider.neutron.list_ports(
  1095         4    1347843.0 336960.8     19.7                  network_id=network.id).get('ports', [])
  1096         4          9.0      2.2      0.0              for port in ports:
  1097                                                           try:
  1098                                                               self.provider.neutron.delete_port(port.get('id'))
  1099                                                           except PortNotFoundClient:
  1100                                                               # Ports could have already been deleted if instances
  1101                                                               # are terminated etc. so exceptions can be safely ignored
  1102                                                               pass
  1103         4    3972874.0 993218.5     58.0              self.provider.neutron.delete_network(network.id)

Total time: 6.84073 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         6          6.0      1.0      0.0          if not network:
   313         6          4.0      0.7      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         6          6.0      1.0      0.0          filters = ['label']
   317         6    6840560.0 1140093.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         5        151.0     30.2      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 6.82445 s
Function: create at line 1211

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1211                                               @dispatch(event="provider.networking.routers.create",
  1212                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1213                                               @profile
  1214                                               def create(self, label, network):
  1215                                                   """Parameter ``network`` is not used by OpenStack."""
  1216         4    6824376.0 1706094.0    100.0          router = self.provider.os_conn.create_router(name=label)
  1217         4         74.0     18.5      0.0          return OpenStackRouter(self.provider, router)

Total time: 6.17932 s
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160         3          6.0      2.0      0.0          try:
  1161         3    6179299.0 2059766.3    100.0              sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162         3          5.0      1.7      0.0              if sn:
  1163         3          6.0      2.0      0.0                  return sn[0]
  1164                                                       # No default subnet look for default network, then create subnet
  1165                                                       net = self.provider.networking.networks.get_or_create_default()
  1166                                                       sn = self.provider.networking.subnets.create(
  1167                                                           label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL,
  1168                                                           cidr_block=OpenStackSubnet.CB_DEFAULT_SUBNET_IPV4RANGE,
  1169                                                           network=net, zone=zone)
  1170                                                       router = self.provider.networking.routers.get_or_create_default(
  1171                                                           net)
  1172                                                       router.attach_subnet(sn)
  1173                                                       gateway = net.gateways.get_or_create()
  1174                                                       router.attach_gateway(gateway)
  1175                                                       return sn
  1176                                                   except NeutronClientException:
  1177                                                       return None

Total time: 4.72856 s
Function: delete at line 1148

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1148                                               @dispatch(event="provider.networking.subnets.delete",
  1149                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1150                                               @profile
  1151                                               def delete(self, subnet):
  1152         3         18.0      6.0      0.0          sn_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
  1153         3    4728545.0 1576181.7    100.0          self.provider.neutron.delete_subnet(sn_id)

Total time: 3.2712 s
Function: label at line 976

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   976                                               @label.setter
   977                                               @profile
   978                                               def label(self, value):  # pylint:disable=arguments-differ
   979                                                   """
   980                                                   Set the router label.
   981                                                   """
   982        11        182.0     16.5      0.0          self.assert_valid_resource_label(value)
   983         3    3271015.0 1090338.3    100.0          self._router = self._provider.os_conn.update_router(self.id, value)

Total time: 3.19342 s
Function: create at line 1307

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1307                                               @dispatch(event="provider.networking.floating_ips.create",
  1308                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1309                                               @profile
  1310                                               def create(self, gateway):
  1311         2          3.0      1.5      0.0          return OpenStackFloatingIP(
  1312         2      51506.0  25753.0      1.6              self.provider, self.provider.os_conn.network.create_ip(
  1313         2    3141916.0 1570958.0     98.4                  floating_network_id=gateway.id))

Total time: 2.73474 s
Function: get at line 1111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1111                                               @dispatch(event="provider.networking.subnets.get",
  1112                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1113                                               @profile
  1114                                               def get(self, subnet_id):
  1115         7         29.0      4.1      0.0          subnet = (s for s in self if s.id == subnet_id)
  1116         7    2734716.0 390673.7    100.0          return next(subnet, None)

Total time: 2.5718 s
Function: list at line 1296

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1296                                               @dispatch(event="provider.networking.floating_ips.list",
  1297                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1298                                               @profile
  1299                                               def list(self, gateway, limit=None, marker=None):
  1300         7         13.0      1.9      0.0          fips = [OpenStackFloatingIP(self.provider, fip)
  1301         7         81.0     11.6      0.0                  for fip in self.provider.os_conn.network.ips(
  1302         7    2571312.0 367330.3    100.0                      floating_network_id=gateway.id
  1303                                                           )]
  1304         7         35.0      5.0      0.0          return ClientPagedResultList(self.provider, fips,
  1305         7        359.0     51.3      0.0                                       limit=limit, marker=marker)

Total time: 2.31206 s
Function: list at line 1193

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1193                                               @dispatch(event="provider.networking.routers.list",
  1194                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1195                                               @profile
  1196                                               def list(self, limit=None, marker=None):
  1197         6    2311586.0 385264.3    100.0          routers = self.provider.os_conn.list_routers()
  1198         6        207.0     34.5      0.0          os_routers = [OpenStackRouter(self.provider, r) for r in routers]
  1199         6         13.0      2.2      0.0          return ClientPagedResultList(self.provider, os_routers, limit=limit,
  1200         6        252.0     42.0      0.0                                       marker=marker)

Total time: 2.07589 s
Function: label at line 877

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   877                                               @label.setter
   878                                               @profile
   879                                               def label(self, value):  # pylint:disable=arguments-differ
   880                                                   """
   881                                                   Set the subnet label.
   882                                                   """
   883        11        180.0     16.4      0.0          self.assert_valid_resource_label(value)
   884         3         22.0      7.3      0.0          self._provider.neutron.update_subnet(
   885         3    2075676.0 691892.0    100.0              self.id, {'subnet': {'name': value or ""}})
   886         3         11.0      3.7      0.0          self._subnet['name'] = value

Total time: 1.94209 s
Function: create at line 1133

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1133                                               @dispatch(event="provider.networking.subnets.create",
  1134                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1135                                               @profile
  1136                                               def create(self, label, network, cidr_block, zone):
  1137                                                   """zone param is ignored."""
  1138        13        160.0     12.3      0.0          OpenStackSubnet.assert_valid_resource_label(label)
  1139         3         11.0      3.7      0.0          network_id = (network.id if isinstance(network, OpenStackNetwork)
  1140                                                                 else network)
  1141         3          3.0      1.0      0.0          subnet_info = {'name': label, 'network_id': network_id,
  1142         3          3.0      1.0      0.0                         'cidr': cidr_block, 'ip_version': 4}
  1143         3    1941847.0 647282.3    100.0          subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
  1144         3         10.0      3.3      0.0                    .get('subnet'))
  1145         3         51.0     17.0      0.0          cb_subnet = OpenStackSubnet(self.provider, subnet)
  1146         3          3.0      1.0      0.0          return cb_subnet

Total time: 1.53474 s
Function: refresh at line 910

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   910                                               @profile
   911                                               def refresh(self):
   912         4    1534726.0 383681.5    100.0          subnet = self._provider.networking.subnets.get(self.id)
   913         4          6.0      1.5      0.0          if subnet:
   914                                                       # pylint:disable=protected-access
   915         1          4.0      4.0      0.0              self._subnet = subnet._subnet
   916         1          2.0      2.0      0.0              self._state = SubnetState.AVAILABLE
   917                                                   else:
   918                                                       # subnet no longer exists
   919         3          6.0      2.0      0.0              self._state = SubnetState.UNKNOWN

Total time: 0.816709 s
Function: find at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.networking.floating_ips.find",
   376                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def find(self, gateway, **kwargs):
   379         3         11.0      3.7      0.0          obj_list = gateway.floating_ips
   380         3          3.0      1.0      0.0          filters = ['name', 'public_ip']
   381         3     816638.0 272212.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   382         2         57.0     28.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.813398 s
Function: get at line 1284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1284                                               @dispatch(event="provider.networking.floating_ips.get",
  1285                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1286                                               @profile
  1287                                               def get(self, gateway, fip_id):
  1288         2          2.0      1.0      0.0          try:
  1289         2          2.0      1.0      0.0              return OpenStackFloatingIP(
  1290         2          2.0      1.0      0.0                  self.provider,
  1291         2     813359.0 406679.5    100.0                  self.provider.os_conn.network.get_ip(fip_id))
  1292         1          4.0      4.0      0.0          except (ResourceNotFound, NotFoundException):
  1293         1          9.0      9.0      0.0              log.debug("Floating IP %s not found.", fip_id)
  1294         1         20.0     20.0      0.0              return None

Total time: 0.732479 s
Function: find at line 1202

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1202                                               @dispatch(event="provider.networking.routers.find",
  1203                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1204                                               @profile
  1205                                               def find(self, **kwargs):
  1206         3          4.0      1.3      0.0          obj_list = self
  1207         3          3.0      1.0      0.0          filters = ['label']
  1208         3     732411.0 244137.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1209         2         61.0     30.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.717092 s
Function: find at line 1052

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1052                                               @dispatch(event="provider.networking.networks.find",
  1053                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1054                                               @profile
  1055                                               def find(self, **kwargs):
  1056         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
  1057                                           
  1058                                                   # All kwargs should have been popped at this time.
  1059         3          5.0      1.7      0.0          if len(kwargs) > 0:
  1060         1          1.0      1.0      0.0              raise InvalidParamException(
  1061         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
  1062         1         15.0     15.0      0.0                  "attributes: %s" % (kwargs, 'label'))
  1063                                           
  1064         2         17.0      8.5      0.0          log.debug("Searching for OpenStack Network with label: %s", label)
  1065         2          4.0      2.0      0.0          networks = [OpenStackNetwork(self.provider, network)
  1066         2         12.0      6.0      0.0                      for network in self.provider.neutron.list_networks(
  1067         2     716908.0 358454.0    100.0                          name=label)
  1068         2         40.0     20.0      0.0                      .get('networks') if network]
  1069         2         83.0     41.5      0.0          return ClientPagedResultList(self.provider, networks)

Total time: 0.663701 s
Function: get at line 1185

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1185                                               @dispatch(event="provider.networking.routers.get",
  1186                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1187                                               @profile
  1188                                               def get(self, router_id):
  1189         2         17.0      8.5      0.0          log.debug("Getting OpenStack Router with the id: %s", router_id)
  1190         2     663665.0 331832.5    100.0          router = self.provider.os_conn.get_router(router_id)
  1191         2         19.0      9.5      0.0          return OpenStackRouter(self.provider, router) if router else None

Total time: 0.416022 s
Function: refresh at line 985

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   985                                               @profile
   986                                               def refresh(self):
   987         1     416022.0 416022.0    100.0          self._router = self._provider.os_conn.get_router(self.id)

Total time: 6e-06 s
Function: delete at line 1261

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1261                                               @dispatch(event="provider.networking.gateways.delete",
  1262                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1263                                               @profile
  1264                                               def delete(self, network, gateway):
  1265         3          6.0      2.0    100.0          pass

