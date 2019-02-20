cloudbridge.test.test_network_service.CloudNetworkServiceTestCase


Test output
 ........
----------------------------------------------------------------------
Ran 8 tests in 487.584s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 108.333 s
Function: delete at line 861

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   861                                               @dispatch(event="provider.networking.networks.delete",
   862                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   863                                               @profile
   864                                               def delete(self, network):
   865                                                   # Accepts network object
   866         4         10.0      2.5      0.0          if isinstance(network, GCPNetwork):
   867         4         13.0      3.2      0.0              name = network.name
   868                                                   # Accepts both name and ID
   869                                                   elif 'googleapis' in network:
   870                                                       name = network.split('/')[-1]
   871                                                   else:
   872                                                       name = network
   873         4      20552.0   5138.0      0.0          response = (self.provider
   874                                                                   .gcp_compute
   875                                                                   .networks()
   876         4         13.0      3.2      0.0                          .delete(project=self.provider.project_name,
   877         4    2847073.0 711768.2      2.6                                  network=name)
   878                                                                   .execute())
   879         4   72369673.0 18092418.2     66.8          self.provider.wait_for_operation(response)
   880                                                   # Remove label
   881         4         19.0      4.8      0.0          tag_name = "_".join(["network", name, "label"])
   882         4   33095185.0 8273796.2     30.5          if not helpers.remove_metadata_item(self.provider, tag_name):
   883                                                       log.warning('No label was found associated with this network '
   884                                                                   '"{}" when deleted.'.format(network))
   885         4         11.0      2.8      0.0          return True

Total time: 80.9144 s
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
   832        14        146.0     10.4      0.0          GCPNetwork.assert_valid_resource_label(label)
   833         4        153.0     38.2      0.0          name = GCPNetwork._generate_name_from_label(label, 'cbnet')
   834         4          6.0      1.5      0.0          body = {'name': name}
   835                                                   # This results in a custom mode network
   836         4          3.0      0.8      0.0          body['autoCreateSubnetworks'] = False
   837         4     842523.0 210630.8      1.0          response = (self.provider
   838                                                                   .gcp_compute
   839                                                                   .networks()
   840         4         19.0      4.8      0.0                          .insert(project=self.provider.project_name,
   841         4    4887307.0 1221826.8      6.0                                  body=body)
   842                                                                   .execute())
   843         4   48797931.0 12199482.8     60.3          self.provider.wait_for_operation(response)
   844         4    1224180.0 306045.0      1.5          cb_net = self.get(name)
   845         4   25162135.0 6290533.8     31.1          cb_net.label = label
   846         4         10.0      2.5      0.0          return cb_net

Total time: 65.0219 s
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
  1045        13        193.0     14.8      0.0          GCPSubnet.assert_valid_resource_label(label)
  1046         3        150.0     50.0      0.0          name = GCPSubnet._generate_name_from_label(label, 'cbsubnet')
  1047         3         22.0      7.3      0.0          region_name = self._zone_to_region(zone)
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
  1060         3          1.0      0.3      0.0          body = {'ipCidrRange': cidr_block,
  1061         3          2.0      0.7      0.0                  'name': name,
  1062         3          9.0      3.0      0.0                  'network': network.resource_url,
  1063         3          3.0      1.0      0.0                  'region': region_name
  1064                                                           }
  1065         3      36027.0  12009.0      0.1          response = (self.provider
  1066                                                                   .gcp_compute
  1067                                                                   .subnetworks()
  1068         3          8.0      2.7      0.0                          .insert(project=self.provider.project_name,
  1069         3          3.0      1.0      0.0                                  region=region_name,
  1070         3    3172088.0 1057362.7      4.9                                  body=body)
  1071                                                                   .execute())
  1072         3   38914855.0 12971618.3     59.8          self.provider.wait_for_operation(response, region=region_name)
  1073         3    1197484.0 399161.3      1.8          cb_subnet = self.get(name)
  1074         3   21701015.0 7233671.7     33.4          cb_subnet.label = label
  1075         3          6.0      2.0      0.0          return cb_subnet

Total time: 60.4918 s
Function: delete at line 1077

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1077                                               @dispatch(event="provider.networking.subnets.delete",
  1078                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1079                                               @profile
  1080                                               def delete(self, subnet):
  1081         3          8.0      2.7      0.0          sn = subnet if isinstance(subnet, GCPSubnet) else self.get(subnet)
  1082         3          4.0      1.3      0.0          if not sn:
  1083                                                       return
  1084         3      25835.0   8611.7      0.0          response = (self.provider
  1085                                                               .gcp_compute
  1086                                                               .subnetworks()
  1087         3          8.0      2.7      0.0                      .delete(project=self.provider.project_name,
  1088         3       1183.0    394.3      0.0                              region=sn.region_name,
  1089         3    2920313.0 973437.7      4.8                              subnetwork=sn.name)
  1090                                                               .execute())
  1091         3   36864675.0 12288225.0     60.9          self.provider.wait_for_operation(response, region=sn.region_name)
  1092                                                   # Remove label
  1093         3         24.0      8.0      0.0          tag_name = "_".join(["subnet", sn.name, "label"])
  1094         3   20679703.0 6893234.3     34.2          if not helpers.remove_metadata_item(self._provider, tag_name):
  1095                                                       log.warning('No label was found associated with this subnet '
  1096                                                                   '"{}" when deleted.'.format(sn.name))

Total time: 49.5131 s
Function: label at line 1305

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1305                                               @label.setter
  1306                                               @profile
  1307                                               def label(self, value):
  1308        15        243.0     16.2      0.0          self.assert_valid_resource_label(value)
  1309         7         36.0      5.1      0.0          tag_name = "_".join(["network", self.name, "label"])
  1310         7   49512783.0 7073254.7    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 47.1401 s
Function: label at line 1565

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1565                                               @label.setter
  1566                                               @profile
  1567                                               def label(self, value):
  1568        14        228.0     16.3      0.0          self.assert_valid_resource_label(value)
  1569         6         30.0      5.0      0.0          tag_name = "_".join(["subnet", self.name, "label"])
  1570         6   47139872.0 7856645.3    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 30.0907 s
Function: label at line 1445

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1445                                               @label.setter
  1446                                               @profile
  1447                                               def label(self, value):
  1448        12        156.0     13.0      0.0          self.assert_valid_resource_label(value)
  1449         4         19.0      4.8      0.0          tag_name = "_".join(["router", self.name, "label"])
  1450         4   30090572.0 7522643.0    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 14.1927 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         6          9.0      1.5      0.0          if not network:
   313         6          3.0      0.5      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         6          5.0      0.8      0.0          filters = ['label']
   317         6   14192347.0 2365391.2    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         5        297.0     59.4      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 12.6716 s
Function: create at line 935

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   935                                               @dispatch(event="provider.networking.routers.create",
   936                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   937                                               @profile
   938                                               def create(self, label, network):
   939         1          3.0      3.0      0.0          log.debug("Creating GCP Router Service with params "
   940         1         11.0     11.0      0.0                    "[label: %s network: %s]", label, network)
   941         1         10.0     10.0      0.0          GCPRouter.assert_valid_resource_label(label)
   942         1         45.0     45.0      0.0          name = GCPRouter._generate_name_from_label(label, 'cb-router')
   943                                           
   944         1          1.0      1.0      0.0          if not isinstance(network, GCPNetwork):
   945                                                       network = self.provider.networking.networks.get(network)
   946         1          3.0      3.0      0.0          network_url = network.resource_url
   947         1          4.0      4.0      0.0          region_name = self.provider.region_name
   948         1      11099.0  11099.0      0.1          response = (self.provider
   949                                                                   .gcp_compute
   950                                                                   .routers()
   951         1          2.0      2.0      0.0                          .insert(project=self.provider.project_name,
   952         1          1.0      1.0      0.0                                  region=region_name,
   953         1          1.0      1.0      0.0                                  body={'name': name,
   954         1     995952.0 995952.0      7.9                                        'network': network_url})
   955                                                                   .execute())
   956         1    2047968.0 2047968.0     16.2          self.provider.wait_for_operation(response, region=region_name)
   957         1     409513.0 409513.0      3.2          cb_router = self.get(name)
   958         1    9206957.0 9206957.0     72.7          cb_router.label = label
   959         1          2.0      2.0      0.0          return cb_router

Total time: 10.1332 s
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
  1108         3          8.0      2.7      0.0          region = self._zone_to_region(zone or self.provider.default_zone,
  1109         3    2048593.0 682864.3     20.2                                        return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111         3    8084553.0 2694851.0     79.8          for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112         3         25.0      8.3      0.0              if sn.region == region.id:
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

Total time: 9.41386 s
Function: list at line 1645

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1645                                               @dispatch(event="provider.networking.floating_ips.list",
  1646                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1647                                               @profile
  1648                                               def list(self, gateway, limit=None, marker=None):
  1649         7         14.0      2.0      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1650         7      26539.0   3791.3      0.3          response = (self.provider
  1651                                                                   .gcp_compute
  1652                                                                   .addresses()
  1653         7         23.0      3.3      0.0                          .list(project=self.provider.project_name,
  1654         7         10.0      1.4      0.0                                region=self.provider.region_name,
  1655         7          6.0      0.9      0.0                                maxResults=max_result,
  1656         7    3276430.0 468061.4     34.8                                pageToken=marker)
  1657                                                                   .execute())
  1658         7         28.0      4.0      0.0          ips = [GCPFloatingIP(self.provider, ip)
  1659         7    6110673.0 872953.3     64.9                 for ip in response.get('items', [])]
  1660         7         25.0      3.6      0.0          if len(ips) > max_result:
  1661                                                       log.warning('Expected at most %d results; got %d',
  1662                                                                   max_result, len(ips))
  1663         7         11.0      1.6      0.0          return ServerPagedResultList('nextPageToken' in response,
  1664         7         14.0      2.0      0.0                                       response.get('nextPageToken'),
  1665         7         83.0     11.9      0.0                                       False, data=ips)

Total time: 8.18624 s
Function: delete at line 1683

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1683                                               @dispatch(event="provider.networking.floating_ips.delete",
  1684                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1685                                               @profile
  1686                                               def delete(self, gateway, fip):
  1687         2          5.0      2.5      0.0          fip = (fip if isinstance(fip, GCPFloatingIP)
  1688         2     813054.0 406527.0      9.9                 else self.get(gateway, fip))
  1689         2          5.0      2.5      0.0          project_name = self.provider.project_name
  1690                                                   # First, delete the forwarding rule, if there is any.
  1691                                                   # pylint:disable=protected-access
  1692         2          2.0      1.0      0.0          if fip._rule:
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
  1704         2       8428.0   4214.0      0.1          response = (self.provider
  1705                                                               .gcp_compute
  1706                                                               .addresses()
  1707         2          3.0      1.5      0.0                      .delete(project=project_name,
  1708         2        820.0    410.0      0.0                              region=fip.region_name,
  1709         2    1470548.0 735274.0     18.0                              address=fip._ip['name'])
  1710                                                               .execute())
  1711         2         15.0      7.5      0.0          self.provider.wait_for_operation(response,
  1712         2    5893359.0 2946679.5     72.0                                           region=fip.region_name)

Total time: 8.02079 s
Function: delete at line 961

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   961                                               @dispatch(event="provider.networking.routers.delete",
   962                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   963                                               @profile
   964                                               def delete(self, router):
   965         1          2.0      2.0      0.0          r = router if isinstance(router, GCPRouter) else self.get(router)
   966         1          1.0      1.0      0.0          if r:
   967         1       7279.0   7279.0      0.1              (self.provider
   968                                                        .gcp_compute
   969                                                        .routers()
   970         1          3.0      3.0      0.0               .delete(project=self.provider.project_name,
   971         1        322.0    322.0      0.0                       region=r.region_name,
   972         1     724805.0 724805.0      9.0                       router=r.name)
   973                                                        .execute())
   974                                                       # Remove label
   975         1          8.0      8.0      0.0              tag_name = "_".join(["router", r.name, "label"])
   976         1    7288365.0 7288365.0     90.9              if not helpers.remove_metadata_item(self.provider, tag_name):
   977                                                           log.warning('No label was found associated with this router '
   978                                                                       '"{}" when deleted.'.format(r.name))

Total time: 7.44141 s
Function: find at line 793

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   793                                               @dispatch(event="provider.networking.networks.find",
   794                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   795                                               @profile
   796                                               def find(self, limit=None, marker=None, **kwargs):
   797                                                   """
   798                                                   GCP networks are global. There is at most one network with a given
   799                                                   name.
   800                                                   """
   801         3          6.0      2.0      0.0          obj_list = self
   802         3          4.0      1.3      0.0          filters = ['name', 'label']
   803         3    7441293.0 2480431.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   804         2          9.0      4.5      0.0          return ClientPagedResultList(self._provider, list(matches),
   805         2         99.0     49.5      0.0                                       limit=limit, marker=marker)

Total time: 7.33389 s
Function: create at line 1667

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1667                                               @dispatch(event="provider.networking.floating_ips.create",
  1668                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1669                                               @profile
  1670                                               def create(self, gateway):
  1671         2          6.0      3.0      0.0          region_name = self.provider.region_name
  1672         2         84.0     42.0      0.0          ip_name = 'ip-{0}'.format(uuid.uuid4())
  1673         2       9381.0   4690.5      0.1          response = (self.provider
  1674                                                               .gcp_compute
  1675                                                               .addresses()
  1676         2          6.0      3.0      0.0                      .insert(project=self.provider.project_name,
  1677         2          2.0      1.0      0.0                              region=region_name,
  1678         2    1808463.0 904231.5     24.7                              body={'name': ip_name})
  1679                                                               .execute())
  1680         2    4779544.0 2389772.0     65.2          self.provider.wait_for_operation(response, region=region_name)
  1681         2     736407.0 368203.5     10.0          return self.get(gateway, ip_name)

Total time: 5.11899 s
Function: get at line 786

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   786                                               @dispatch(event="provider.networking.networks.get",
   787                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   788                                               @profile
   789                                               def get(self, network_id):
   790        18    5118527.0 284362.6    100.0          network = self.provider.get_resource('networks', network_id)
   791        18        463.0     25.7      0.0          return GCPNetwork(self.provider, network) if network else None

Total time: 4.15656 s
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
  1010        17         28.0      1.6      0.0          filter = None
  1011        17         20.0      1.2      0.0          if network is not None:
  1012         6         11.0      1.8      0.0              network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014         6         32.0      5.3      0.0              filter = 'network eq %s' % network.resource_url
  1015        17         17.0      1.0      0.0          if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018        17         41.0      2.4      0.0              region_name = self.provider.region_name
  1019        17         14.0      0.8      0.0          subnets = []
  1020        17     160142.0   9420.1      3.9          response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023        17         53.0      3.1      0.0                          .list(project=self.provider.project_name,
  1024        17         13.0      0.8      0.0                                region=region_name,
  1025        17    3994482.0 234969.5     96.1                                filter=filter)
  1026                                                                   .execute())
  1027       104        169.0      1.6      0.0          for subnet in response.get('items', []):
  1028        87        684.0      7.9      0.0              subnets.append(GCPSubnet(self.provider, subnet))
  1029        17         39.0      2.3      0.0          return ClientPagedResultList(self.provider, subnets,
  1030        17        819.0     48.2      0.0                                       limit=limit, marker=marker)

Total time: 3.60639 s
Function: get at line 996

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   996                                               @dispatch(event="provider.networking.subnets.get",
   997                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
   998                                               @profile
   999                                               def get(self, subnet_id):
  1000         9    3606281.0 400697.9    100.0          subnet = self.provider.get_resource('subnetworks', subnet_id)
  1001         9        113.0     12.6      0.0          return GCPSubnet(self.provider, subnet) if subnet else None

Total time: 2.69905 s
Function: find at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.networking.floating_ips.find",
   376                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def find(self, gateway, **kwargs):
   379         3          9.0      3.0      0.0          obj_list = gateway.floating_ips
   380         3          3.0      1.0      0.0          filters = ['name', 'public_ip']
   381         3    2698959.0 899653.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   382         2         76.0     38.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 2.2592 s
Function: get at line 1637

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1637                                               @dispatch(event="provider.networking.floating_ips.get",
  1638                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1639                                               @profile
  1640                                               def get(self, gateway, floating_ip_id):
  1641         6    2259067.0 376511.2    100.0          fip = self.provider.get_resource('addresses', floating_ip_id)
  1642                                                   return (GCPFloatingIP(self.provider, fip)
  1643         6        135.0     22.5      0.0                  if fip else None)

Total time: 2.17036 s
Function: list at line 807

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   807                                               @dispatch(event="provider.networking.networks.list",
   808                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   809                                               @profile
   810                                               def list(self, limit=None, marker=None, filter=None):
   811                                                   # TODO: Decide whether we keep filter in 'list'
   812         8         11.0      1.4      0.0          networks = []
   813         8      44096.0   5512.0      2.0          response = (self.provider
   814                                                                   .gcp_compute
   815                                                                   .networks()
   816         8         25.0      3.1      0.0                          .list(project=self.provider.project_name,
   817         8    2124440.0 265555.0     97.9                                filter=filter)
   818                                                                   .execute())
   819        86        117.0      1.4      0.0          for network in response.get('items', []):
   820        78       1260.0     16.2      0.1              networks.append(GCPNetwork(self.provider, network))
   821         8         16.0      2.0      0.0          return ClientPagedResultList(self.provider, networks,
   822         8        399.0     49.9      0.0                                       limit=limit, marker=marker)

Total time: 1.97249 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         3          8.0      2.7      0.0          region = self.provider.get_resource('regions', region_id,
   387         3    1972413.0 657471.0    100.0                                              region=region_id)
   388         3         73.0     24.3      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 1.71609 s
Function: refresh at line 1603

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1603                                               @profile
  1604                                               def refresh(self):
  1605         4    1716073.0 429018.2    100.0          subnet = self._provider.networking.subnets.get(self.id)
  1606         4          4.0      1.0      0.0          if subnet:
  1607                                                       # pylint:disable=protected-access
  1608         1          4.0      4.0      0.0              self._subnet = subnet._subnet
  1609                                                   else:
  1610                                                       # subnet no longer exists
  1611         3          8.0      2.7      0.0              self._subnet['status'] = SubnetState.UNKNOWN

Total time: 1.3876 s
Function: get at line 893

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   893                                               @dispatch(event="provider.networking.routers.get",
   894                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   895                                               @profile
   896                                               def get(self, router_id):
   897         4          8.0      2.0      0.0          router = self.provider.get_resource(
   898         4    1387531.0 346882.8    100.0              'routers', router_id, region=self.provider.region_name)
   899         4         63.0     15.8      0.0          return GCPRouter(self.provider, router) if router else None

Total time: 1.36571 s
Function: list at line 911

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   911                                               @dispatch(event="provider.networking.routers.list",
   912                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   913                                               @profile
   914                                               def list(self, limit=None, marker=None):
   915         6         21.0      3.5      0.0          region = self.provider.region_name
   916         6          8.0      1.3      0.0          max_result = limit if limit is not None and limit < 500 else 500
   917         6      48768.0   8128.0      3.6          response = (self.provider
   918                                                                   .gcp_compute
   919                                                                   .routers()
   920         6         17.0      2.8      0.0                          .list(project=self.provider.project_name,
   921         6          4.0      0.7      0.0                                region=region,
   922         6          4.0      0.7      0.0                                maxResults=max_result,
   923         6    1316670.0 219445.0     96.4                                pageToken=marker)
   924                                                                   .execute())
   925         6         18.0      3.0      0.0          routers = []
   926        11         20.0      1.8      0.0          for router in response.get('items', []):
   927         5         88.0     17.6      0.0              routers.append(GCPRouter(self.provider, router))
   928         6         10.0      1.7      0.0          if len(routers) > max_result:
   929                                                       log.warning('Expected at most %d results; go %d',
   930                                                                   max_result, len(routers))
   931         6         10.0      1.7      0.0          return ServerPagedResultList('nextPageToken' in response,
   932         6         10.0      1.7      0.0                                       response.get('nextPageToken'),
   933         6         64.0     10.7      0.0                                       False, data=routers)

Total time: 1.34887 s
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342         5    1348850.0 269770.0    100.0          net = self._provider.networking.networks.get(self.id)
  1343         5          5.0      1.0      0.0          if net:
  1344                                                       # pylint:disable=protected-access
  1345         1          3.0      3.0      0.0              self._network = net._network
  1346                                                   else:
  1347                                                       # network no longer exists
  1348         4         12.0      3.0      0.0              self._network['status'] = NetworkState.UNKNOWN

Total time: 1.33483 s
Function: find at line 901

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   901                                               @dispatch(event="provider.networking.routers.find",
   902                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   903                                               @profile
   904                                               def find(self, limit=None, marker=None, **kwargs):
   905         3          7.0      2.3      0.0          obj_list = self
   906         3          4.0      1.3      0.0          filters = ['name', 'label']
   907         3    1334720.0 444906.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   908         2          9.0      4.5      0.0          return ClientPagedResultList(self._provider, list(matches),
   909         2         91.0     45.5      0.0                                       limit=limit, marker=marker)

Total time: 0.267038 s
Function: refresh at line 1457

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1457                                               @profile
  1458                                               def refresh(self):
  1459         1     267033.0 267033.0    100.0          router = self._provider.networking.routers.get(self.id)
  1460         1          2.0      2.0      0.0          if router:
  1461                                                       # pylint:disable=protected-access
  1462         1          3.0      3.0      0.0              self._router = router._router
  1463                                                   else:
  1464                                                       # router no longer exists
  1465                                                       self._router['status'] = RouterState.UNKNOWN

Total time: 5e-06 s
Function: get_or_create at line 1610

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1610                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1611                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1612                                               @profile
  1613                                               def get_or_create(self, network):
  1614         3          5.0      1.7    100.0          return self._default_internet_gateway

