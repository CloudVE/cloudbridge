cloudbridge.test.test_security_service.CloudSecurityServiceTestCase


Test output
 ..........
----------------------------------------------------------------------
Ran 10 tests in 64.346s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 13.7187 s
Function: create at line 250

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   250                                               @cb_helpers.deprecated_alias(network_id='network')
   251                                               @dispatch(event="provider.security.vm_firewalls.create",
   252                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   253                                               @profile
   254                                               def create(self, label, network, description=None):
   255        16        214.0     13.4      0.0          OpenStackVMFirewall.assert_valid_resource_label(label)
   256         6         12.0      2.0      0.0          net_id = network.id if isinstance(network, Network) else network
   257                                                   # We generally simulate a network being associated with a firewall
   258                                                   # by storing the supplied value in the firewall description field that
   259                                                   # is not modifiable after creation; however, because of some networking
   260                                                   # specificity in Nectar, we must also allow an empty network id value.
   261         6          2.0      0.3      0.0          if not net_id:
   262                                                       net_id = ""
   263         6          5.0      0.8      0.0          if not description:
   264                                                       description = ""
   265         6          8.0      1.3      0.0          description += " [{}{}]".format(OpenStackVMFirewall._network_id_tag,
   266         6         20.0      3.3      0.0                                          net_id)
   267         6    8942449.0 1490408.2     65.2          sg = self.provider.os_conn.network.create_security_group(
   268         6    4775806.0 795967.7     34.8              name=label, description=description)
   269         6         16.0      2.7      0.0          if sg:
   270         6        153.0     25.5      0.0              return OpenStackVMFirewall(self.provider, sg)
   271                                                   return None

Total time: 12.5863 s
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160         6         11.0      1.8      0.0          try:
  1161         6   12586255.0 2097709.2    100.0              sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162         6          8.0      1.3      0.0              if sn:
  1163         6         14.0      2.3      0.0                  return sn[0]
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

Total time: 12.5242 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         6          5.0      0.8      0.0          if not network:
   313         6          3.0      0.5      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         6          4.0      0.7      0.0          filters = ['label']
   317         6   12523991.0 2087331.8    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         6        192.0     32.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 12.466 s
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122         6          6.0      1.0      0.0          if network:
  1123                                                       network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125                                                       subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128         6          5.0      0.8      0.0              subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129         6   12465724.0 2077620.7    100.0                         self.provider.neutron.list_subnets().get('subnets', [])]
  1130         6         23.0      3.8      0.0          return ClientPagedResultList(self.provider, subnets,
  1131         6        274.0     45.7      0.0                                       limit=limit, marker=marker)

Total time: 8.52707 s
Function: create at line 190

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   190                                               @dispatch(event="provider.security.key_pairs.create",
   191                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   192                                               @profile
   193                                               def create(self, name, public_key_material=None):
   194        14        144.0     10.3      0.0          OpenStackKeyPair.assert_valid_resource_name(name)
   195         4    6556322.0 1639080.5     76.9          existing_kp = self.find(name=name)
   196         4          4.0      1.0      0.0          if existing_kp:
   197         1          1.0      1.0      0.0              raise DuplicateResourceException(
   198         1          5.0      5.0      0.0                  'Keypair already exists with name {0}'.format(name))
   199                                           
   200         3          3.0      1.0      0.0          private_key = None
   201         3          3.0      1.0      0.0          if not public_key_material:
   202         2     159987.0  79993.5      1.9              public_key_material, private_key = cb_helpers.generate_key_pair()
   203                                           
   204         3         21.0      7.0      0.0          kp = self.provider.nova.keypairs.create(name,
   205         3    1810523.0 603507.7     21.2                                                  public_key=public_key_material)
   206         3         53.0     17.7      0.0          cb_kp = OpenStackKeyPair(self.provider, kp)
   207         3          9.0      3.0      0.0          cb_kp.material = private_key
   208         3          0.0      0.0      0.0          return cb_kp

Total time: 7.93536 s
Function: find at line 172

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   172                                               @dispatch(event="provider.security.key_pairs.find",
   173                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   174                                               @profile
   175                                               def find(self, **kwargs):
   176         7         11.0      1.6      0.0          name = kwargs.pop('name', None)
   177                                           
   178                                                   # All kwargs should have been popped at this time.
   179         7          9.0      1.3      0.0          if len(kwargs) > 0:
   180         1          1.0      1.0      0.0              raise InvalidParamException(
   181         1          0.0      0.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   182         1         14.0     14.0      0.0                  "attributes: %s" % (kwargs, 'name'))
   183                                           
   184         6    7935006.0 1322501.0    100.0          keypairs = self.provider.nova.keypairs.findall(name=name)
   185         6         18.0      3.0      0.0          results = [OpenStackKeyPair(self.provider, kp)
   186         6         41.0      6.8      0.0                     for kp in keypairs]
   187         6         53.0      8.8      0.0          log.debug("Searching for %s in: %s", name, keypairs)
   188         6        210.0     35.0      0.0          return ClientPagedResultList(self.provider, results)

Total time: 4.68369 s
Function: refresh at line 1172

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1172                                               @profile
  1173                                               def refresh(self):
  1174        13        174.0     13.4      0.0          self._vm_firewall = self._provider.os_conn.network.get_security_group(
  1175        13    4683518.0 360270.6    100.0              self.id)

Total time: 4.02541 s
Function: create at line 299

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   299                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   300                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   301                                               @profile
   302                                               def create(self, firewall, direction, protocol=None, from_port=None,
   303                                                          to_port=None, cidr=None, src_dest_fw=None):
   304         5          7.0      1.4      0.0          src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
   305         5         22.0      4.4      0.0                                                         OpenStackVMFirewall)
   306         4          2.0      0.5      0.0                            else src_dest_fw)
   307                                           
   308         5          4.0      0.8      0.0          try:
   309         5          9.0      1.8      0.0              if direction == TrafficDirection.INBOUND:
   310         5          4.0      0.8      0.0                  os_direction = 'ingress'
   311                                                       elif direction == TrafficDirection.OUTBOUND:
   312                                                           os_direction = 'egress'
   313                                                       else:
   314                                                           raise InvalidValueException("direction", direction)
   315                                                       # pylint:disable=protected-access
   316         5         47.0      9.4      0.0              rule = self.provider.os_conn.network.create_security_group_rule(
   317         5         53.0     10.6      0.0                  security_group_id=firewall.id,
   318         5          5.0      1.0      0.0                  direction=os_direction,
   319         5          4.0      0.8      0.0                  port_range_max=to_port,
   320         5          3.0      0.6      0.0                  port_range_min=from_port,
   321         5          5.0      1.0      0.0                  protocol=protocol,
   322         5          5.0      1.0      0.0                  remote_ip_prefix=cidr,
   323         5    1943972.0 388794.4     48.3                  remote_group_id=src_dest_fw_id)
   324         4    1391281.0 347820.2     34.6              firewall.refresh()
   325         4     304324.0  76081.0      7.6              return OpenStackVMFirewallRule(firewall, rule.to_dict())
   326         1          3.0      3.0      0.0          except HttpException as e:
   327         1     366160.0 366160.0      9.1              firewall.refresh()
   328                                                       # 409=Conflict, raised for duplicate rule
   329         1          3.0      3.0      0.0              if e.status_code == 409:
   330         1          2.0      2.0      0.0                  existing = self.find(firewall, direction=direction,
   331         1          0.0      0.0      0.0                                       protocol=protocol, from_port=from_port,
   332         1          1.0      1.0      0.0                                       to_port=to_port, cidr=cidr,
   333         1      19471.0  19471.0      0.5                                       src_dest_fw_id=src_dest_fw_id)
   334         1         24.0     24.0      0.0                  return existing[0]
   335                                                       else:
   336                                                           raise e

Total time: 3.07443 s
Function: delete at line 338

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   338                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   339                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   340                                               @profile
   341                                               def delete(self, firewall, rule):
   342         4         33.0      8.2      0.0          rule_id = (rule.id if isinstance(rule, OpenStackVMFirewallRule)
   343                                                              else rule)
   344         4    1656371.0 414092.8     53.9          self.provider.os_conn.network.delete_security_group_rule(rule_id)
   345         4    1418026.0 354506.5     46.1          firewall.refresh()

Total time: 2.89585 s
Function: list at line 154

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   154                                               @dispatch(event="provider.security.key_pairs.list",
   155                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   156                                               @profile
   157                                               def list(self, limit=None, marker=None):
   158                                                   """
   159                                                   List all key pairs associated with this account.
   160                                           
   161                                                   :rtype: ``list`` of :class:`.KeyPair`
   162                                                   :return:  list of KeyPair objects
   163                                                   """
   164         4    2895613.0 723903.2    100.0          keypairs = self.provider.nova.keypairs.list()
   165         4         13.0      3.2      0.0          results = [OpenStackKeyPair(self.provider, kp)
   166         4         51.0     12.8      0.0                     for kp in keypairs]
   167         4          7.0      1.8      0.0          log.debug("Listing all key pairs associated with OpenStack "
   168         4         32.0      8.0      0.0                    "Account: %s", results)
   169         4          9.0      2.2      0.0          return ClientPagedResultList(self.provider, results,
   170         4        127.0     31.8      0.0                                       limit=limit, marker=marker)

Total time: 2.59937 s
Function: get at line 226

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   226                                               @dispatch(event="provider.security.vm_firewalls.get",
   227                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   228                                               @profile
   229                                               def get(self, vm_firewall_id):
   230         7          8.0      1.1      0.0          try:
   231         7          7.0      1.0      0.0              return OpenStackVMFirewall(
   232         7         13.0      1.9      0.0                  self.provider,
   233         7         61.0      8.7      0.0                  self.provider.os_conn.network
   234         7    2599251.0 371321.6    100.0                      .get_security_group(vm_firewall_id))
   235         1          4.0      4.0      0.0          except (ResourceNotFound, NotFoundException):
   236         1          9.0      9.0      0.0              log.debug("Firewall %s not found.", vm_firewall_id)
   237         1         20.0     20.0      0.0              return None

Total time: 2.56676 s
Function: list at line 239

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   239                                               @dispatch(event="provider.security.vm_firewalls.list",
   240                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   241                                               @profile
   242                                               def list(self, limit=None, marker=None):
   243                                                   firewalls = [
   244         7         12.0      1.7      0.0              OpenStackVMFirewall(self.provider, fw)
   245         7    2566492.0 366641.7    100.0              for fw in self.provider.os_conn.network.security_groups()]
   246                                           
   247         7         23.0      3.3      0.0          return ClientPagedResultList(self.provider, firewalls,
   248         7        236.0     33.7      0.0                                       limit=limit, marker=marker)

Total time: 2.56556 s
Function: get at line 139

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   139                                               @dispatch(event="provider.security.key_pairs.get",
   140                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   141                                               @profile
   142                                               def get(self, key_pair_id):
   143                                                   """
   144                                                   Returns a KeyPair given its id.
   145                                                   """
   146         4         33.0      8.2      0.0          log.debug("Returning KeyPair with the id %s", key_pair_id)
   147         4          2.0      0.5      0.0          try:
   148         4          3.0      0.8      0.0              return OpenStackKeyPair(
   149         4    2565479.0 641369.8    100.0                  self.provider, self.provider.nova.keypairs.get(key_pair_id))
   150         1          4.0      4.0      0.0          except NovaNotFound:
   151         1          9.0      9.0      0.0              log.debug("KeyPair %s was not found.", key_pair_id)
   152         1         32.0     32.0      0.0              return None

Total time: 2.45924 s
Function: delete at line 273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   273                                               @dispatch(event="provider.security.vm_firewalls.delete",
   274                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   275                                               @profile
   276                                               def delete(self, vm_firewall):
   277         6         10.0      1.7      0.0          fw = (vm_firewall if isinstance(vm_firewall, OpenStackVMFirewall)
   278                                                         else self.get(vm_firewall))
   279         6          5.0      0.8      0.0          if fw:
   280                                                       # pylint:disable=protected-access
   281         6    2459225.0 409870.8    100.0              fw._vm_firewall.delete(self.provider.os_conn.session)

Total time: 2.39136 s
Function: get at line 1035

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1035                                               @dispatch(event="provider.networking.networks.get",
  1036                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1037                                               @profile
  1038                                               def get(self, network_id):
  1039         6         16.0      2.7      0.0          network = (n for n in self if n.id == network_id)
  1040         6    2391344.0 398557.3    100.0          return next(network, None)

Total time: 2.3219 s
Function: label at line 1159

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1159                                               @label.setter
  1160                                               # pylint:disable=arguments-differ
  1161                                               @profile
  1162                                               def label(self, value):
  1163        11        202.0     18.4      0.0          self.assert_valid_resource_label(value)
  1164         3         33.0     11.0      0.0          self._provider.os_conn.network.update_security_group(
  1165         3    1108031.0 369343.7     47.7              self.id, name=value or "")
  1166         3    1213633.0 404544.3     52.3          self.refresh()

Total time: 2.31848 s
Function: list at line 1042

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1042                                               @dispatch(event="provider.networking.networks.list",
  1043                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1044                                               @profile
  1045                                               def list(self, limit=None, marker=None):
  1046         6          8.0      1.3      0.0          networks = [OpenStackNetwork(self.provider, network)
  1047         6    2317780.0 386296.7    100.0                      for network in self.provider.neutron.list_networks()
  1048         6        433.0     72.2      0.0                      .get('networks') if network]
  1049         6         12.0      2.0      0.0          return ClientPagedResultList(self.provider, networks,
  1050         6        243.0     40.5      0.0                                       limit=limit, marker=marker)

Total time: 2.28191 s
Function: delete at line 210

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   210                                               @dispatch(event="provider.security.key_pairs.delete",
   211                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   212                                               @profile
   213                                               def delete(self, key_pair):
   214         3          5.0      1.7      0.0          keypair = (key_pair if isinstance(key_pair, OpenStackKeyPair)
   215         1     517605.0 517605.0     22.7                     else self.get(key_pair))
   216         3          4.0      1.3      0.0          if keypair:
   217                                                       # pylint:disable=protected-access
   218         3    1764294.0 588098.0     77.3              keypair._key_pair.delete()

Total time: 0.725505 s
Function: find at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @dispatch(event="provider.security.vm_firewalls.find",
    82                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    83                                               @profile
    84                                               def find(self, **kwargs):
    85         3          3.0      1.0      0.0          obj_list = self
    86         3          3.0      1.0      0.0          filters = ['label']
    87         3     725442.0 241814.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
    88                                           
    89                                                   # All kwargs should have been popped at this time.
    90         2          3.0      1.5      0.0          if len(kwargs) > 0:
    91                                                       raise InvalidParamException(
    92                                                           "Unrecognised parameters for search: %s. Supported "
    93                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
    94                                           
    95         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider,
    96         2         51.0     25.5      0.0                                       matches if matches else [])

Total time: 0.407367 s
Function: list at line 289

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   289                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   290                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   291                                               @profile
   292                                               def list(self, firewall, limit=None, marker=None):
   293                                                   # pylint:disable=protected-access
   294        16         28.0      1.8      0.0          rules = [OpenStackVMFirewallRule(firewall, r)
   295        16     406870.0  25429.4     99.9                   for r in firewall._vm_firewall.security_group_rules]
   296        16         35.0      2.2      0.0          return ClientPagedResultList(self.provider, rules,
   297        16        434.0     27.1      0.1                                       limit=limit, marker=marker)

Total time: 0.012727 s
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125         4         11.0      2.8      0.1          obj_list = firewall.rules
   126         4          4.0      1.0      0.0          filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127         4          4.0      1.0      0.0                     'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128         4      12632.0   3158.0     99.3          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129         3         76.0     25.3      0.6          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.00037 s
Function: get at line 111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   111                                               @dispatch(event="provider.security.vm_firewall_rules.get",
   112                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   113                                               @profile
   114                                               def get(self, firewall, rule_id):
   115         2        366.0    183.0     98.9          matches = [rule for rule in firewall.rules if rule.id == rule_id]
   116         2          2.0      1.0      0.5          if matches:
   117         1          1.0      1.0      0.3              return matches[0]
   118                                                   else:
   119         1          1.0      1.0      0.3              return None

