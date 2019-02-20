cloudbridge.test.test_network_service.CloudNetworkServiceTestCase


Test output
 ........
----------------------------------------------------------------------
Ran 8 tests in 685.382s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 190.776 s
Function: label at line 957

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   957                                               @label.setter
   958                                               # pylint:disable=arguments-differ
   959                                               @profile
   960                                               def label(self, value):
   961        14        168.0     12.0      0.0          self.assert_valid_resource_label(value)
   962         6    1815558.0 302593.0      1.0          network = self.network
   963                                                   # pylint:disable=protected-access
   964         6          6.0      1.0      0.0          az_network = network._network
   965         6         33.0      5.5      0.0          kwargs = {self.tag_name: value or ""}
   966         6          8.0      1.3      0.0          az_network.tags.update(**kwargs)
   967         6         42.0      7.0      0.0          self._provider.azure_client.update_network_tags(
   968         6  188960422.0 31493403.7     99.0              az_network.id, az_network)

Total time: 127.148 s
Function: delete at line 1308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1308                                               @dispatch(event="provider.networking.subnets.delete",
  1309                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1310                                               @profile
  1311                                               def delete(self, subnet):
  1312         3          5.0      1.7      0.0          sn = subnet if isinstance(subnet, AzureSubnet) else self.get(subnet)
  1313         3          2.0      0.7      0.0          if sn:
  1314         3   32107906.0 10702635.3     25.3              self.provider.azure_client.delete_subnet(sn.id)
  1315                                                       # Although Subnet doesn't support labels, we use the parent
  1316                                                       # Network's tags to track the subnet's labels, thus that
  1317                                                       # network-level tag must be deleted with the subnet
  1318         3        169.0     56.3      0.0              net_id = sn.network_id
  1319         3     916549.0 305516.3      0.7              az_network = self.provider.azure_client.get_network(net_id)
  1320         3         16.0      5.3      0.0              az_network.tags.pop(sn.tag_name)
  1321         3         22.0      7.3      0.0              self.provider.azure_client.update_network_tags(
  1322         3   94123007.0 31374335.7     74.0                  az_network.id, az_network)

Total time: 107.812 s
Function: create at line 1283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1283                                               @dispatch(event="provider.networking.subnets.create",
  1284                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1285                                               @profile
  1286                                               def create(self, label, network, cidr_block, zone):
  1287        13        176.0     13.5      0.0          AzureSubnet.assert_valid_resource_label(label)
  1288                                                   # Although Subnet doesn't support tags in Azure, we use the parent
  1289                                                   # Network's tags to track its subnets' labels
  1290         3        157.0     52.3      0.0          subnet_name = AzureSubnet._generate_name_from_label(label, "cb-sn")
  1291                                           
  1292                                                   network_id = network.id \
  1293         3         12.0      4.0      0.0              if isinstance(network, Network) else network
  1294                                           
  1295         3         17.0      5.7      0.0          subnet_info = self.provider.azure_client\
  1296                                                       .create_subnet(
  1297         3         11.0      3.7      0.0                  network_id,
  1298         3         22.0      7.3      0.0                  subnet_name,
  1299                                                           {
  1300         3   12313650.0 4104550.0     11.4                      'address_prefix': cidr_block
  1301                                                           }
  1302                                                       )
  1303                                           
  1304         3         61.0     20.3      0.0          subnet = AzureSubnet(self.provider, subnet_info)
  1305         3   95497765.0 31832588.3     88.6          subnet.label = label
  1306         3          5.0      1.7      0.0          return subnet

Total time: 94.4434 s
Function: label at line 757

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   757                                               @label.setter
   758                                               # pylint:disable=arguments-differ
   759                                               @profile
   760                                               def label(self, value):
   761                                                   """
   762                                                   Set the network label.
   763                                                   """
   764        11        141.0     12.8      0.0          self.assert_valid_resource_label(value)
   765         3         14.0      4.7      0.0          self._network.tags.update(Label=value or "")
   766         3         20.0      6.7      0.0          self._provider.azure_client. \
   767         3   94443273.0 31481091.0    100.0              update_network_tags(self.id, self._network)

Total time: 94.3677 s
Function: label at line 1461

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1461                                               @label.setter
  1462                                               # pylint:disable=arguments-differ
  1463                                               @profile
  1464                                               def label(self, value):
  1465                                                   """
  1466                                                   Set the router label.
  1467                                                   """
  1468        11        156.0     14.2      0.0          self.assert_valid_resource_label(value)
  1469         3         10.0      3.3      0.0          self._route_table.tags.update(Label=value or "")
  1470         3         19.0      6.3      0.0          self._provider.azure_client. \
  1471         3          3.0      1.0      0.0              update_route_table_tags(self._route_table.name,
  1472         3   94367482.0 31455827.3    100.0                                      self._route_table)

Total time: 22.1054 s
Function: delete at line 1468

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1468                                               @dispatch(event="provider.networking.floating_ips.delete",
  1469                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1470                                               @profile
  1471                                               def delete(self, gateway, fip):
  1472         2          5.0      2.5      0.0          fip_id = fip.id if isinstance(fip, AzureFloatingIP) else fip
  1473         2   22105367.0 11052683.5    100.0          self.provider.azure_client.delete_floating_ip(fip_id)

Total time: 19.7348 s
Function: create at line 1189

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1189                                               @dispatch(event="provider.networking.networks.create",
  1190                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1191                                               @profile
  1192                                               def create(self, label, cidr_block):
  1193        14        176.0     12.6      0.0          AzureNetwork.assert_valid_resource_label(label)
  1194                                                   params = {
  1195         4    1410464.0 352616.0      7.1              'location': self.provider.azure_client.region_name,
  1196                                                       'address_space': {
  1197         4         11.0      2.8      0.0                  'address_prefixes': [cidr_block]
  1198                                                       },
  1199         4         12.0      3.0      0.0              'tags': {'Label': label}
  1200                                                   }
  1201                                           
  1202         4        208.0     52.0      0.0          network_name = AzureNetwork._generate_name_from_label(label, 'cb-net')
  1203                                           
  1204         4         23.0      5.8      0.0          az_network = self.provider.azure_client.create_network(network_name,
  1205         4   18323820.0 4580955.0     92.9                                                                 params)
  1206         4        124.0     31.0      0.0          cb_network = AzureNetwork(self.provider, az_network)
  1207         4          2.0      0.5      0.0          return cb_network

Total time: 11.9861 s
Function: create at line 1369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1369                                               @dispatch(event="provider.networking.routers.create",
  1370                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1371                                               @profile
  1372                                               def create(self, label, network):
  1373         1         64.0     64.0      0.0          router_name = AzureRouter._generate_name_from_label(label, "cb-router")
  1374                                           
  1375         1          6.0      6.0      0.0          parameters = {"location": self.provider.region_name,
  1376         1          1.0      1.0      0.0                        "tags": {'Label': label}}
  1377                                           
  1378         1         10.0     10.0      0.0          route = self.provider.azure_client. \
  1379         1   11985961.0 11985961.0    100.0              create_route_table(router_name, parameters)
  1380         1         25.0     25.0      0.0          return AzureRouter(self.provider, route)

Total time: 11.5771 s
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172        46         52.0      1.1      0.0          try:
  1173        46   11575576.0 251643.0    100.0              network = self.provider.azure_client.get_network(network_id)
  1174        45       1350.0     30.0      0.0              return AzureNetwork(self.provider, network)
  1175         1          4.0      4.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177         1        126.0    126.0      0.0              log.exception(cloud_error)
  1178         1          1.0      1.0      0.0              return None

Total time: 11.1098 s
Function: delete at line 1382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1382                                               @dispatch(event="provider.networking.routers.delete",
  1383                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1384                                               @profile
  1385                                               def delete(self, router):
  1386         1          2.0      2.0      0.0          r = router if isinstance(router, AzureRouter) else self.get(router)
  1387         1          0.0      0.0      0.0          if r:
  1388         1   11109796.0 11109796.0    100.0              self.provider.azure_client.delete_route_table(r.name)

Total time: 10.0241 s
Function: create at line 1452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1452                                               @dispatch(event="provider.networking.floating_ips.create",
  1453                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1454                                               @profile
  1455                                               def create(self, gateway):
  1456                                                   public_ip_parameters = {
  1457         2         31.0     15.5      0.0              'location': self.provider.azure_client.region_name,
  1458         2          5.0      2.5      0.0              'public_ip_allocation_method': 'Static'
  1459                                                   }
  1460                                           
  1461         2          8.0      4.0      0.0          public_ip_name = AzureFloatingIP._generate_name_from_label(
  1462         2        118.0     59.0      0.0              None, 'cb-fip-')
  1463                                           
  1464         2         11.0      5.5      0.0          floating_ip = self.provider.azure_client.\
  1465         2   10023918.0 5011959.0    100.0              create_floating_ip(public_ip_name, public_ip_parameters)
  1466         2         42.0     21.0      0.0          return AzureFloatingIP(self.provider, floating_ip)

Total time: 7.66637 s
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276         6    4676201.0 779366.8     61.0          obj_list = self._list_subnets(network)
  1277         6         16.0      2.7      0.0          filters = ['label']
  1278         6    2989973.0 498328.8     39.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280         5         12.0      2.4      0.0          return ClientPagedResultList(self.provider,
  1281         5        167.0     33.4      0.0                                       matches if matches else [])

Total time: 5.74256 s
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184        18         24.0      1.3      0.0          networks = [AzureNetwork(self.provider, network)
  1185        18    5741811.0 318989.5    100.0                      for network in self.provider.azure_client.list_networks()]
  1186        18         62.0      3.4      0.0          return ClientPagedResultList(self.provider, networks,
  1187        18        662.0     36.8      0.0                                       limit=limit, marker=marker)

Total time: 5.57723 s
Function: list at line 1264

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1264                                               @dispatch(event="provider.networking.subnets.list",
  1265                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1266                                               @profile
  1267                                               def list(self, network=None, limit=None, marker=None):
  1268        11         28.0      2.5      0.0          return ClientPagedResultList(self.provider,
  1269        11    5576772.0 506979.3    100.0                                       self._list_subnets(network),
  1270        11        428.0     38.9      0.0                                       limit=limit, marker=marker)

Total time: 4.13445 s
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323         3    4134440.0 1378146.7    100.0          matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324         3          3.0      1.0      0.0          if matches:
   325         3          5.0      1.7      0.0              return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 1.65222 s
Function: list at line 1442

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1442                                               @dispatch(event="provider.networking.floating_ips.list",
  1443                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1444                                               @profile
  1445                                               def list(self, gateway, limit=None, marker=None):
  1446         7         12.0      1.7      0.0          floating_ips = [AzureFloatingIP(self.provider, floating_ip)
  1447         7    1651954.0 235993.4    100.0                          for floating_ip in self.provider.azure_client.
  1448                                                                   list_floating_ips()]
  1449         7         24.0      3.4      0.0          return ClientPagedResultList(self.provider, floating_ips,
  1450         7        230.0     32.9      0.0                                       limit=limit, marker=marker)

Total time: 1.55898 s
Function: refresh at line 1474

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1474                                               @profile
  1475                                               def refresh(self):
  1476         6         49.0      8.2      0.0          self._route_table = self._provider.azure_client. \
  1477         6    1558927.0 259821.2    100.0              get_route_table(self._route_table.name)

Total time: 1.50925 s
Function: refresh at line 782

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   782                                               @profile
   783                                               def refresh(self):
   784                                                   """
   785                                                   Refreshes the state of this network by re-querying the cloud provider
   786                                                   for its latest state.
   787                                                   """
   788         5         18.0      3.6      0.0          try:
   789         5         74.0     14.8      0.0              self._network = self._provider.azure_client.\
   790         5    1508606.0 301721.2    100.0                  get_network(self.id)
   791         1          2.0      2.0      0.0              self._state = self._network.provisioning_state
   792         4         11.0      2.8      0.0          except (CloudError, ValueError) as cloud_error:
   793         4        531.0    132.8      0.0              log.exception(cloud_error.message)
   794                                                       # The network no longer exists and cannot be refreshed.
   795                                                       # set the state to unknown
   796         4          8.0      2.0      0.0              self._state = 'unknown'

Total time: 1.44414 s
Function: list at line 1358

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1358                                               @dispatch(event="provider.networking.routers.list",
  1359                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1360                                               @profile
  1361                                               def list(self, limit=None, marker=None):
  1362         6         10.0      1.7      0.0          routes = [AzureRouter(self.provider, route)
  1363                                                             for route in
  1364         6    1443836.0 240639.3    100.0                    self.provider.azure_client.list_route_tables()]
  1365         6         32.0      5.3      0.0          return ClientPagedResultList(self.provider,
  1366         6          4.0      0.7      0.0                                       routes,
  1367         6        259.0     43.2      0.0                                       limit=limit, marker=marker)

Total time: 1.06759 s
Function: refresh at line 999

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   999                                               @profile
  1000                                               def refresh(self):
  1001                                                   """
  1002                                                   Refreshes the state of this network by re-querying the cloud provider
  1003                                                   for its latest state.
  1004                                                   """
  1005         4         16.0      4.0      0.0          try:
  1006         4         53.0     13.2      0.0              self._subnet = self._provider.azure_client. \
  1007         4    1067113.0 266778.2    100.0                  get_subnet(self.id)
  1008         1          5.0      5.0      0.0              self._state = self._subnet.provisioning_state
  1009         3          7.0      2.3      0.0          except (CloudError, ValueError) as cloud_error:
  1010         3        388.0    129.3      0.0              log.exception(cloud_error.message)
  1011                                                       # The subnet no longer exists and cannot be refreshed.
  1012                                                       # set the state to unknown
  1013         3         13.0      4.3      0.0              self._state = 'unknown'

Total time: 0.710938 s
Function: get at line 1430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1430                                               @dispatch(event="provider.networking.floating_ips.get",
  1431                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1432                                               @profile
  1433                                               def get(self, gateway, fip_id):
  1434         2          3.0      1.5      0.0          try:
  1435         2     710652.0 355326.0    100.0              az_ip = self.provider.azure_client.get_floating_ip(fip_id)
  1436         1          4.0      4.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1437                                                       # Azure raises the cloud error if the resource not available
  1438         1        264.0    264.0      0.0              log.exception(cloud_error)
  1439         1          1.0      1.0      0.0              return None
  1440         1         14.0     14.0      0.0          return AzureFloatingIP(self.provider, az_ip)

Total time: 0.518986 s
Function: get at line 1329

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1329                                               @dispatch(event="provider.networking.routers.get",
  1330                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1331                                               @profile
  1332                                               def get(self, router_id):
  1333         2          2.0      1.0      0.0          try:
  1334         2     518821.0 259410.5    100.0              route = self.provider.azure_client.get_route_table(router_id)
  1335         1         17.0     17.0      0.0              return AzureRouter(self.provider, route)
  1336         1          3.0      3.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1337                                                       # Azure raises the cloud error if the resource not available
  1338         1        141.0    141.0      0.0              log.exception(cloud_error)
  1339         1          2.0      2.0      0.0              return None

Total time: 0.487832 s
Function: find at line 283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   283                                               @dispatch(event="provider.networking.networks.find",
   284                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   285                                               @profile
   286                                               def find(self, **kwargs):
   287         3          4.0      1.3      0.0          obj_list = self
   288         3          3.0      1.0      0.0          filters = ['label']
   289         3     487780.0 162593.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   290                                           
   291                                                   # All kwargs should have been popped at this time.
   292         2          2.0      1.0      0.0          if len(kwargs) > 0:
   293                                                       raise TypeError("Unrecognised parameters for search: %s."
   294                                                                       " Supported attributes: %s" % (kwargs,
   295                                                                                                      ", ".join(filters)))
   296                                           
   297         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider,
   298         2         40.0     20.0      0.0                                       matches if matches else [])

Total time: 0.478273 s
Function: find at line 1341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1341                                               @dispatch(event="provider.networking.routers.find",
  1342                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1343                                               @profile
  1344                                               def find(self, **kwargs):
  1345         3          8.0      2.7      0.0          obj_list = self
  1346         3          4.0      1.3      0.0          filters = ['label']
  1347         3     478208.0 159402.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1348                                           
  1349                                                   # All kwargs should have been popped at this time.
  1350         2          2.0      1.0      0.0          if len(kwargs) > 0:
  1351                                                       raise InvalidParamException(
  1352                                                           "Unrecognised parameters for search: %s. Supported "
  1353                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
  1354                                           
  1355         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider,
  1356         2         48.0     24.0      0.0                                       matches if matches else [])

Total time: 0.429782 s
Function: find at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.networking.floating_ips.find",
   376                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def find(self, gateway, **kwargs):
   379         3         16.0      5.3      0.0          obj_list = gateway.floating_ips
   380         3          3.0      1.0      0.0          filters = ['name', 'public_ip']
   381         3     429720.0 143240.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   382         2         43.0     21.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.302909 s
Function: get at line 1245

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1245                                               @dispatch(event="provider.networking.subnets.get",
  1246                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1247                                               @profile
  1248                                               def get(self, subnet_id):
  1249                                                   """
  1250                                                    Azure does not provide an api to get the subnet directly by id.
  1251                                                    It also requires the network id.
  1252                                                    To make it consistent across the providers the following code
  1253                                                    gets the specific code from the subnet list.
  1254                                                   """
  1255         2          3.0      1.5      0.0          try:
  1256         2     302739.0 151369.5     99.9              azure_subnet = self.provider.azure_client.get_subnet(subnet_id)
  1257                                                       return AzureSubnet(self.provider,
  1258         1         16.0     16.0      0.0                                 azure_subnet) if azure_subnet else None
  1259         1          2.0      2.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1260                                                       # Azure raises the cloud error if the resource not available
  1261         1        147.0    147.0      0.0              log.exception(cloud_error)
  1262         1          2.0      2.0      0.0              return None

Total time: 0.14658 s
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113         1          2.0      2.0      0.0          region = None
  1114         3     146507.0  48835.7    100.0          for azureRegion in self.provider.azure_client.list_locations():
  1115         3          4.0      1.3      0.0              if azureRegion.name == region_id:
  1116         1         23.0     23.0      0.0                  region = AzureRegion(self.provider, azureRegion)
  1117         1         43.0     43.0      0.0                  break
  1118         1          1.0      1.0      0.0          return region

Total time: 0.000112 s
Function: get_or_create at line 1403

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1403                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1404                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1405                                               @profile
  1406                                               def get_or_create(self, network):
  1407         3        112.0     37.3    100.0          return self._gateway_singleton(network)

