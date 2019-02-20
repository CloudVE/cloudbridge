cloudbridge.test.test_security_service.CloudSecurityServiceTestCase


Test output
 ..........
----------------------------------------------------------------------
Ran 10 tests in 424.495s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 135.951 s
Function: delete at line 222

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   222                                               @dispatch(event="provider.security.vm_firewalls.delete",
   223                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   224                                               @profile
   225                                               def delete(self, vm_firewall):
   226         6        107.0     17.8      0.0          fw_id = (vm_firewall.id if isinstance(vm_firewall, GCPVMFirewall)
   227                                                            else vm_firewall)
   228         6  135950603.0 22658433.8    100.0          return self._delegate.delete_tag_network_with_id(fw_id)

Total time: 95.6242 s
Function: create_with_priority at line 284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   284                                               @profile
   285                                               def create_with_priority(self, firewall, direction, protocol, priority,
   286                                                                        from_port=None, to_port=None, cidr=None,
   287                                                                        src_dest_fw=None):
   288        11         46.0      4.2      0.0          port = GCPVMFirewallRuleService.to_port_range(from_port, to_port)
   289        11         11.0      1.0      0.0          src_dest_tag = None
   290        11          8.0      0.7      0.0          src_dest_fw_id = None
   291        11          8.0      0.7      0.0          if src_dest_fw:
   292         1          2.0      2.0      0.0              src_dest_tag = src_dest_fw.name
   293         1         24.0     24.0      0.0              src_dest_fw_id = src_dest_fw.id
   294        11         34.0      3.1      0.0          if not firewall.delegate.add_firewall(
   295        11         32.0      2.9      0.0                  firewall.name, direction, protocol, priority, port, cidr,
   296        11         38.0      3.5      0.0                  src_dest_tag, firewall.description,
   297        11   95433532.0 8675775.6     99.8                  firewall.network.name):
   298                                                       return None
   299        11         45.0      4.1      0.0          rules = self.find(firewall, direction=direction, protocol=protocol,
   300        11         13.0      1.2      0.0                            from_port=from_port, to_port=to_port, cidr=cidr,
   301        11     190339.0  17303.5      0.2                            src_dest_fw_id=src_dest_fw_id)
   302        11         12.0      1.1      0.0          if len(rules) < 1:
   303         6          2.0      0.3      0.0              return None
   304         5          9.0      1.8      0.0          return rules[0]

Total time: 92.3823 s
Function: create at line 205

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   205                                               @dispatch(event="provider.security.vm_firewalls.create",
   206                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   207                                               @profile
   208                                               def create(self, label, network, description=None):
   209        16        222.0     13.9      0.0          GCPVMFirewall.assert_valid_resource_label(label)
   210         6         14.0      2.3      0.0          network = (network if isinstance(network, GCPNetwork)
   211         6    2195956.0 365992.7      2.4                     else self.provider.networking.networks.get(network))
   212         6        165.0     27.5      0.0          fw = GCPVMFirewall(self._delegate, label, network, description)
   213         6   43930059.0 7321676.5     47.6          fw.label = label
   214                                                   # This rule exists implicitly. Add it explicitly so that the firewall
   215                                                   # is not empty and the rule is shown by list/get/find methods.
   216                                                   # pylint:disable=protected-access
   217         6         71.0     11.8      0.0          self.provider.security._vm_firewall_rules.create_with_priority(
   218         6         24.0      4.0      0.0              fw, direction=TrafficDirection.OUTBOUND, protocol='tcp',
   219         6   46255807.0 7709301.2     50.1              priority=65534, cidr='0.0.0.0/0')
   220         6          2.0      0.3      0.0          return fw

Total time: 66.1447 s
Function: label at line 482

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   482                                               @label.setter
   483                                               @profile
   484                                               def label(self, value):
   485        17        256.0     15.1      0.0          self.assert_valid_resource_label(value)
   486         9         47.0      5.2      0.0          tag_name = "_".join(["firewall", self.name, "label"])
   487         9   66144423.0 7349380.3    100.0          helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 49.3686 s
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   307                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, firewall, direction, protocol, from_port=None,
   310                                                          to_port=None, cidr=None, src_dest_fw=None):
   311         5          6.0      1.2      0.0          return self.create_with_priority(firewall, direction, protocol,
   312         5          4.0      0.8      0.0                                           1000, from_port, to_port, cidr,
   313         5   49368624.0 9873724.8    100.0                                           src_dest_fw)

Total time: 28.7511 s
Function: delete at line 315

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   315                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   316                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   317                                               @profile
   318                                               def delete(self, firewall, rule):
   319         2          3.0      1.5      0.0          rule = (rule if isinstance(rule, GCPVMFirewallRule)
   320                                                           else self.get(firewall, rule))
   321         2        426.0    213.0      0.0          if rule.is_dummy_rule():
   322                                                       return True
   323         2   28750687.0 14375343.5    100.0          firewall.delegate.delete_firewall_id(rule._rule)

Total time: 26.1585 s
Function: create at line 137

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   137                                               @dispatch(event="provider.security.key_pairs.create",
   138                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   139                                               @profile
   140                                               def create(self, name, public_key_material=None):
   141        14        143.0     10.2      0.0          GCPKeyPair.assert_valid_resource_name(name)
   142         4          2.0      0.5      0.0          private_key = None
   143         4          4.0      1.0      0.0          if not public_key_material:
   144         3     234767.0  78255.7      0.9              public_key_material, private_key = cb_helpers.generate_key_pair()
   145                                                   # TODO: Add support for other formats not assume ssh-rsa
   146         1          1.0      1.0      0.0          elif "ssh-rsa" not in public_key_material:
   147                                                       public_key_material = "ssh-rsa {}".format(public_key_material)
   148         4         20.0      5.0      0.0          kp_info = GCPKeyPair.GCPKeyInfo(name, public_key_material)
   149         4        182.0     45.5      0.0          metadata_value = json.dumps(kp_info._asdict())
   150         4          3.0      0.8      0.0          try:
   151         4          9.0      2.2      0.0              helpers.add_metadata_item(self.provider,
   152         4          5.0      1.2      0.0                                        GCPKeyPair.KP_TAG_PREFIX + name,
   153         4   25923184.0 6480796.0     99.1                                        metadata_value)
   154         3         65.0     21.7      0.0              return GCPKeyPair(self.provider, kp_info, private_key)
   155         1          5.0      5.0      0.0          except googleapiclient.errors.HttpError as err:
   156         1          4.0      4.0      0.0              if err.resp.get('content-type', '').startswith('application/json'):
   157         1         62.0     62.0      0.0                  message = (json.loads(err.content).get('error', {})
   158         1          3.0      3.0      0.0                             .get('errors', [{}])[0].get('message'))
   159         1          2.0      2.0      0.0                  if "duplicate keys" in message:
   160         1          2.0      2.0      0.0                      raise DuplicateResourceException(
   161         1          7.0      7.0      0.0                          'A KeyPair with name {0} already exists'.format(name))
   162                                                       raise

Total time: 20.4335 s
Function: delete at line 164

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   164                                               @dispatch(event="provider.security.key_pairs.delete",
   165                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   166                                               @profile
   167                                               def delete(self, key_pair):
   168         3          7.0      2.3      0.0          key_pair = (key_pair if isinstance(key_pair, GCPKeyPair) else
   169         3     520539.0 173513.0      2.5                      self.get(key_pair))
   170         3          2.0      0.7      0.0          if key_pair:
   171         3          4.0      1.3      0.0              helpers.remove_metadata_item(
   172         3   19912993.0 6637664.3     97.5                  self.provider, GCPKeyPair.KP_TAG_PREFIX + key_pair.name)

Total time: 20.1145 s
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
  1108         6         13.0      2.2      0.0          region = self._zone_to_region(zone or self.provider.default_zone,
  1109         6    3993255.0 665542.5     19.9                                        return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111         6   16121125.0 2686854.2     80.1          for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112         6         46.0      7.7      0.0              if sn.region == region.id:
  1113         6         16.0      2.7      0.0                  return sn
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

Total time: 19.1619 s
Function: get at line 786

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   786                                               @dispatch(event="provider.networking.networks.get",
   787                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   788                                               @profile
   789                                               def get(self, network_id):
   790        61   19159803.0 314095.1    100.0          network = self.provider.get_resource('networks', network_id)
   791        61       2126.0     34.9      0.0          return GCPNetwork(self.provider, network) if network else None

Total time: 16.0481 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         6          6.0      1.0      0.0          if not network:
   313         6          5.0      0.8      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         6          5.0      0.8      0.0          filters = ['label']
   317         6   16047845.0 2674640.8    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         6        282.0     47.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 14.4078 s
Function: list at line 192

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   192                                               @dispatch(event="provider.security.vm_firewalls.list",
   193                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   194                                               @profile
   195                                               def list(self, limit=None, marker=None):
   196         8         16.0      2.0      0.0          vm_firewalls = []
   197        54      16425.0    304.2      0.1          for tag, network_name in self._delegate.tag_networks:
   198        46        347.0      7.5      0.0              network = self.provider.networking.networks.get(
   199        46   14389298.0 312810.8     99.9                      network_name)
   200        46       1055.0     22.9      0.0              vm_firewall = GCPVMFirewall(self._delegate, tag, network)
   201        46         73.0      1.6      0.0              vm_firewalls.append(vm_firewall)
   202         8         27.0      3.4      0.0          return ClientPagedResultList(self.provider, vm_firewalls,
   203         8        566.0     70.8      0.0                                       limit=limit, marker=marker)

Total time: 8.39101 s
Function: find at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @dispatch(event="provider.security.vm_firewalls.find",
    82                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    83                                               @profile
    84                                               def find(self, **kwargs):
    85         3          6.0      2.0      0.0          obj_list = self
    86         3          4.0      1.3      0.0          filters = ['label']
    87         3    8390891.0 2796963.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
    88                                           
    89                                                   # All kwargs should have been popped at this time.
    90         2          6.0      3.0      0.0          if len(kwargs) > 0:
    91                                                       raise InvalidParamException(
    92                                                           "Unrecognised parameters for search: %s. Supported "
    93                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
    94                                           
    95         2         10.0      5.0      0.0          return ClientPagedResultList(self.provider,
    96         2         89.0     44.5      0.0                                       matches if matches else [])

Total time: 3.93347 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         6         12.0      2.0      0.0          region = self.provider.get_resource('regions', region_id,
   387         6    3933318.0 655553.0    100.0                                              region=region_id)
   388         6        138.0     23.0      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 2.33161 s
Function: list at line 104

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   104                                               @dispatch(event="provider.security.key_pairs.list",
   105                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   106                                               @profile
   107                                               def list(self, limit=None, marker=None):
   108        12         12.0      1.0      0.0          key_pairs = []
   109        12         16.0      1.3      0.0          for item in helpers.find_matching_metadata_items(
   110        59    2329791.0  39488.0     99.9                  self.provider, GCPKeyPair.KP_TAG_REGEX):
   111        47        690.0     14.7      0.0              metadata_value = json.loads(item['value'])
   112        47        194.0      4.1      0.0              kp_info = GCPKeyPair.GCPKeyInfo(**metadata_value)
   113        47        412.0      8.8      0.0              key_pairs.append(GCPKeyPair(self.provider, kp_info))
   114        12         17.0      1.4      0.0          return ClientPagedResultList(self.provider, key_pairs,
   115        12        475.0     39.6      0.0                                       limit=limit, marker=marker)

Total time: 1.39911 s
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
  1010         6          4.0      0.7      0.0          filter = None
  1011         6          5.0      0.8      0.0          if network is not None:
  1012                                                       network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014                                                       filter = 'network eq %s' % network.resource_url
  1015         6          2.0      0.3      0.0          if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018         6          8.0      1.3      0.0              region_name = self.provider.region_name
  1019         6          3.0      0.5      0.0          subnets = []
  1020         6      59042.0   9840.3      4.2          response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023         6         15.0      2.5      0.0                          .list(project=self.provider.project_name,
  1024         6          4.0      0.7      0.0                                region=region_name,
  1025         6    1339305.0 223217.5     95.7                                filter=filter)
  1026                                                                   .execute())
  1027        48         70.0      1.5      0.0          for subnet in response.get('items', []):
  1028        42        326.0      7.8      0.0              subnets.append(GCPSubnet(self.provider, subnet))
  1029         6         12.0      2.0      0.0          return ClientPagedResultList(self.provider, subnets,
  1030         6        311.0     51.8      0.0                                       limit=limit, marker=marker)

Total time: 1.11951 s
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
    98        25    1119442.0  44777.7    100.0          for kp in self:
    99        24         40.0      1.7      0.0              if kp.id == key_pair_id:
   100         5         30.0      6.0      0.0                  return kp
   101                                                   else:
   102         1          1.0      1.0      0.0              return None

Total time: 0.897284 s
Function: get at line 181

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   181                                               @dispatch(event="provider.security.vm_firewalls.get",
   182                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   183                                               @profile
   184                                               def get(self, vm_firewall_id):
   185                                                   tag, network_name = \
   186         4       7801.0   1950.2      0.9              self._delegate.get_tag_network_from_id(vm_firewall_id)
   187         4          5.0      1.2      0.0          if tag is None:
   188         1          1.0      1.0      0.0              return None
   189         3     889408.0 296469.3     99.1          network = self.provider.networking.networks.get(network_name)
   190         3         69.0     23.0      0.0          return GCPVMFirewall(self._delegate, tag, network)

Total time: 0.409439 s
Function: find at line 117

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   117                                               @dispatch(event="provider.security.key_pairs.find",
   118                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   119                                               @profile
   120                                               def find(self, **kwargs):
   121                                                   """
   122                                                   Searches for a key pair by a given list of attributes.
   123                                                   """
   124         3          3.0      1.0      0.0          obj_list = self
   125         3          3.0      1.0      0.0          filters = ['id', 'name']
   126         3     409375.0 136458.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   127                                           
   128                                                   # All kwargs should have been popped at this time.
   129         2          2.0      1.0      0.0          if len(kwargs) > 0:
   130                                                       raise InvalidParamException(
   131                                                           "Unrecognised parameters for search: %s. Supported "
   132                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   133                                           
   134         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider,
   135         2         53.0     26.5      0.0                                       matches if matches else [])

Total time: 0.243234 s
Function: refresh at line 542

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   542                                               @profile
   543                                               def refresh(self):
   544         1     243228.0 243228.0    100.0          fw = self._provider.security.vm_firewalls.get(self.id)
   545                                                   # restore all internal state
   546         1          1.0      1.0      0.0          if fw:
   547                                                       # pylint:disable=protected-access
   548         1          1.0      1.0      0.0              self._delegate = fw._delegate
   549                                                       # pylint:disable=protected-access
   550         1          1.0      1.0      0.0              self._description = fw._description
   551                                                       # pylint:disable=protected-access
   552         1          1.0      1.0      0.0              self._network = fw._network
   553                                                       # pylint:disable=protected-access
   554         1          2.0      2.0      0.0              self._rule_container = fw._rule_container

Total time: 0.125725 s
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125        14         49.0      3.5      0.0          obj_list = firewall.rules
   126        14         12.0      0.9      0.0          filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127        14         13.0      0.9      0.0                     'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128        14     125412.0   8958.0     99.8          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129        13        239.0     18.4      0.2          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.093306 s
Function: list at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   255                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   256                                               @profile
   257                                               def list(self, firewall, limit=None, marker=None):
   258        26         32.0      1.2      0.0          rules = []
   259        26         61.0      2.3      0.1          for fw in firewall.delegate.iter_firewalls(
   260        66      10237.0    155.1     11.0                  firewall.name, firewall.network.name):
   261        40      56163.0   1404.1     60.2              rule = GCPVMFirewallRule(firewall, fw['id'])
   262        40      25970.0    649.2     27.8              if rule.is_dummy_rule():
   263        26         62.0      2.4      0.1                  self._dummy_rule = rule
   264                                                       else:
   265        14         16.0      1.1      0.0                  rules.append(rule)
   266        26         45.0      1.7      0.0          return ClientPagedResultList(self.provider, rules,
   267        26        720.0     27.7      0.8                                       limit=limit, marker=marker)

Total time: 0.007167 s
Function: get at line 111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   111                                               @dispatch(event="provider.security.vm_firewall_rules.get",
   112                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   113                                               @profile
   114                                               def get(self, firewall, rule_id):
   115         2       7166.0   3583.0    100.0          matches = [rule for rule in firewall.rules if rule.id == rule_id]
   116         2          0.0      0.0      0.0          if matches:
   117         1          1.0      1.0      0.0              return matches[0]
   118                                                   else:
   119         1          0.0      0.0      0.0              return None

