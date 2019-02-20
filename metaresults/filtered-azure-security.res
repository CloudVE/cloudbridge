cloudbridge.test.test_security_service.CloudSecurityServiceTestCase


Test output
 ..........
----------------------------------------------------------------------
Ran 10 tests in 848.776s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 491.5 s
Function: create at line 113

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   113                                               @cb_helpers.deprecated_alias(network_id='network')
   114                                               @dispatch(event="provider.security.vm_firewalls.create",
   115                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   116                                               @profile
   117                                               def create(self, label, network, description=None):
   118        16        219.0     13.7      0.0          AzureVMFirewall.assert_valid_resource_label(label)
   119         6        304.0     50.7      0.0          name = AzureVMFirewall._generate_name_from_label(label, "cb-fw")
   120         6         17.0      2.8      0.0          net = network.id if isinstance(network, Network) else network
   121         6         15.0      2.5      0.0          parameters = {"location": self.provider.region_name,
   122         6          5.0      0.8      0.0                        "tags": {'Label': label,
   123         6         12.0      2.0      0.0                                 'network_id': net}}
   124                                           
   125         6          4.0      0.7      0.0          if description:
   126         6         12.0      2.0      0.0              parameters['tags'].update(Description=description)
   127                                           
   128         6         32.0      5.3      0.0          fw = self.provider.azure_client.create_vm_firewall(name,
   129         6   28271830.0 4711971.7      5.8                                                             parameters)
   130                                           
   131                                                   # Add default rules to negate azure default rules.
   132                                                   # See: https://github.com/CloudVE/cloudbridge/issues/106
   133                                                   # pylint:disable=protected-access
   134        42        125.0      3.0      0.0          for rule in fw.default_security_rules:
   135        36         70.0      1.9      0.0              rule_name = "cb-override-" + rule.name
   136                                                       # Transpose rules to priority 4001 onwards, because
   137                                                       # only 0-4096 are allowed for custom rules
   138        36         68.0      1.9      0.0              rule.priority = rule.priority - 61440
   139        36         47.0      1.3      0.0              rule.access = "Deny"
   140        36        320.0      8.9      0.0              self.provider.azure_client.create_vm_firewall_rule(
   141        36  396826984.0 11022971.8     80.7                  fw.id, rule_name, rule)
   142                                           
   143                                                   # Add a new custom rule allowing all outbound traffic to the internet
   144         6          6.0      1.0      0.0          parameters = {"priority": 3000,
   145         6          6.0      1.0      0.0                        "protocol": "*",
   146         6          6.0      1.0      0.0                        "source_port_range": "*",
   147         6          6.0      1.0      0.0                        "source_address_prefix": "*",
   148         6          6.0      1.0      0.0                        "destination_port_range": "*",
   149         6          7.0      1.2      0.0                        "destination_address_prefix": "Internet",
   150         6          6.0      1.0      0.0                        "access": "Allow",
   151         6         24.0      4.0      0.0                        "direction": "Outbound"}
   152         6         56.0      9.3      0.0          result = self.provider.azure_client.create_vm_firewall_rule(
   153         6   66399658.0 11066609.7     13.5              fw.id, "cb-default-internet-outbound", parameters)
   154         6         23.0      3.8      0.0          fw.security_rules.append(result)
   155                                           
   156         6        181.0     30.2      0.0          cb_fw = AzureVMFirewall(self.provider, fw)
   157         6          7.0      1.2      0.0          return cb_fw

Total time: 179.261 s
Function: delete at line 159

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   159                                               @dispatch(event="provider.security.vm_firewalls.delete",
   160                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   161                                               @profile
   162                                               def delete(self, vm_firewall):
   163         6         23.0      3.8      0.0          fw_id = (vm_firewall.id if isinstance(vm_firewall, AzureVMFirewall)
   164                                                            else vm_firewall)
   165         6  179261294.0 29876882.3    100.0          self.provider.azure_client.delete_vm_firewall(fw_id)

Total time: 67.5466 s
Function: label at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @label.setter
    82                                               @profile
    83                                               def label(self, value):
    84        11        137.0     12.5      0.0          self.assert_valid_resource_label(value)
    85         3         12.0      4.0      0.0          self._vm_firewall.tags.update(Label=value or "")
    86         3         20.0      6.7      0.0          self._provider.azure_client.update_vm_firewall_tags(
    87         3   67546411.0 22515470.3    100.0              self.id, self._vm_firewall.tags)

Total time: 55.53 s
Function: create at line 187

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   187                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   188                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   189                                               @profile
   190                                               def create(self, firewall, direction, protocol=None, from_port=None,
   191                                                          to_port=None, cidr=None, src_dest_fw=None):
   192         5          8.0      1.6      0.0          if protocol and from_port and to_port:
   193         5          6.0      1.2      0.0              return self._create_rule(firewall, direction, protocol, from_port,
   194         5   55529974.0 11105994.8    100.0                                       to_port, cidr)
   195                                                   elif src_dest_fw:
   196                                                       result = None
   197                                                       fw = (self.provider.security.vm_firewalls.get(src_dest_fw)
   198                                                             if isinstance(src_dest_fw, str) else src_dest_fw)
   199                                                       for rule in fw.rules:
   200                                                           result = self._create_rule(
   201                                                               rule.direction, rule.protocol, rule.from_port,
   202                                                               rule.to_port, rule.cidr)
   203                                                       return result
   204                                                   else:
   205                                                       return None

Total time: 32.3408 s
Function: delete at line 238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   238                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   239                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   240                                               @profile
   241                                               def delete(self, firewall, rule):
   242         3          9.0      3.0      0.0          rule_id = rule.id if isinstance(rule, AzureVMFirewallRule) else rule
   243         3          7.0      2.3      0.0          fw_name = firewall.name
   244         3         14.0      4.7      0.0          self.provider.azure_client. \
   245         3   32340706.0 10780235.3    100.0              delete_vm_firewall_rule(rule_id, fw_name)
   246         4         35.0      8.8      0.0          for i, o in enumerate(firewall._vm_firewall.security_rules):
   247         4         10.0      2.5      0.0              if o.id == rule_id:
   248                                                           # pylint:disable=protected-access
   249         3          6.0      2.0      0.0                  del firewall._vm_firewall.security_rules[i]
   250         3          3.0      1.0      0.0                  break

Total time: 9.13897 s
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323         6    9138951.0 1523158.5    100.0          matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324         6          6.0      1.0      0.0          if matches:
   325         6         14.0      2.3      0.0              return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 9.07843 s
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276         6    5803094.0 967182.3     63.9          obj_list = self._list_subnets(network)
  1277         6         15.0      2.5      0.0          filters = ['label']
  1278         6    3275043.0 545840.5     36.1          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280         6         40.0      6.7      0.0          return ClientPagedResultList(self.provider,
  1281         6        234.0     39.0      0.0                                       matches if matches else [])

Total time: 6.12621 s
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.key_pairs.create",
   307                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, name, public_key_material=None):
   310        14        165.0     11.8      0.0          AzureKeyPair.assert_valid_resource_name(name)
   311         4    5249153.0 1312288.2     85.7          key_pair = self.get(name)
   312                                           
   313         4          5.0      1.2      0.0          if key_pair:
   314         1          1.0      1.0      0.0              raise DuplicateResourceException(
   315         1          4.0      4.0      0.0                  'Keypair already exists with name {0}'.format(name))
   316                                           
   317         3          2.0      0.7      0.0          private_key = None
   318         3          3.0      1.0      0.0          if not public_key_material:
   319         2     109145.0  54572.5      1.8              public_key_material, private_key = cb_helpers.generate_key_pair()
   320                                           
   321                                                   entity = {
   322         3         15.0      5.0      0.0              'PartitionKey': AzureKeyPairService.PARTITION_KEY,
   323         3        135.0     45.0      0.0              'RowKey': str(uuid.uuid4()),
   324         3          2.0      0.7      0.0              'Name': name,
   325         3          7.0      2.3      0.0              'Key': public_key_material
   326                                                   }
   327                                           
   328         3     372582.0 124194.0      6.1          self.provider.azure_client.create_public_key(entity)
   329         3     394977.0 131659.0      6.4          key_pair = self.get(name)
   330         3         12.0      4.0      0.0          key_pair.material = private_key
   331         3          2.0      0.7      0.0          return key_pair

Total time: 6.12568 s
Function: get at line 259

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   259                                               @dispatch(event="provider.security.key_pairs.get",
   260                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   261                                               @profile
   262                                               def get(self, key_pair_id):
   263        11         13.0      1.2      0.0          try:
   264        11    1125460.0 102314.5     18.4              key_pair = self.provider.azure_client.\
   265        11    5000048.0 454549.8     81.6                  get_public_key(key_pair_id)
   266                                           
   267        11         23.0      2.1      0.0              if key_pair:
   268         7        135.0     19.3      0.0                  return AzureKeyPair(self.provider, key_pair)
   269         4          3.0      0.8      0.0              return None
   270                                                   except AzureException as error:
   271                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   272                                                       log.debug(error)
   273                                                       return None

Total time: 4.61747 s
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172        18         23.0      1.3      0.0          try:
  1173        18    4616908.0 256494.9    100.0              network = self.provider.azure_client.get_network(network_id)
  1174        18        542.0     30.1      0.0              return AzureNetwork(self.provider, network)
  1175                                                   except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177                                                       log.exception(cloud_error)
  1178                                                       return None

Total time: 4.32446 s
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184         6         10.0      1.7      0.0          networks = [AzureNetwork(self.provider, network)
  1185         6    4324209.0 720701.5    100.0                      for network in self.provider.azure_client.list_networks()]
  1186         6         20.0      3.3      0.0          return ClientPagedResultList(self.provider, networks,
  1187         6        221.0     36.8      0.0                                       limit=limit, marker=marker)

Total time: 1.84706 s
Function: list at line 105

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   105                                               @dispatch(event="provider.security.vm_firewalls.list",
   106                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   107                                               @profile
   108                                               def list(self, limit=None, marker=None):
   109         7         13.0      1.9      0.0          fws = [AzureVMFirewall(self.provider, fw)
   110         7    1846776.0 263825.1    100.0                 for fw in self.provider.azure_client.list_vm_firewall()]
   111         7        274.0     39.1      0.0          return ClientPagedResultList(self.provider, fws, limit, marker)

Total time: 0.751486 s
Function: list at line 275

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   275                                               @dispatch(event="provider.security.key_pairs.list",
   276                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   277                                               @profile
   278                                               def list(self, limit=None, marker=None):
   279         6         39.0      6.5      0.0          key_pairs, resume_marker = self.provider.azure_client.list_public_keys(
   280         6          7.0      1.2      0.0              AzureKeyPairService.PARTITION_KEY, marker=marker,
   281         6     751263.0 125210.5    100.0              limit=limit or self.provider.config.default_result_limit)
   282         6         19.0      3.2      0.0          results = [AzureKeyPair(self.provider, key_pair)
   283         6         82.0     13.7      0.0                     for key_pair in key_pairs]
   284         6          6.0      1.0      0.0          return ServerPagedResultList(is_truncated=resume_marker,
   285         6          4.0      0.7      0.0                                       marker=resume_marker,
   286         6          4.0      0.7      0.0                                       supports_total=False,
   287         6         62.0     10.3      0.0                                       data=results)

Total time: 0.726115 s
Function: get at line 93

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    93                                               @dispatch(event="provider.security.vm_firewalls.get",
    94                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    95                                               @profile
    96                                               def get(self, vm_firewall_id):
    97         3          2.0      0.7      0.0          try:
    98         3     725867.0 241955.7    100.0              fws = self.provider.azure_client.get_vm_firewall(vm_firewall_id)
    99         2         45.0     22.5      0.0              return AzureVMFirewall(self.provider, fws)
   100         1          4.0      4.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
   101                                                       # Azure raises the cloud error if the resource not available
   102         1        196.0    196.0      0.0              log.exception(cloud_error)
   103         1          1.0      1.0      0.0              return None

Total time: 0.553877 s
Function: find at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @dispatch(event="provider.security.vm_firewalls.find",
    82                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    83                                               @profile
    84                                               def find(self, **kwargs):
    85         3          4.0      1.3      0.0          obj_list = self
    86         3          4.0      1.3      0.0          filters = ['label']
    87         3     553824.0 184608.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
    88                                           
    89                                                   # All kwargs should have been popped at this time.
    90         2          2.0      1.0      0.0          if len(kwargs) > 0:
    91                                                       raise InvalidParamException(
    92                                                           "Unrecognised parameters for search: %s. Supported "
    93                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
    94                                           
    95         2          2.0      1.0      0.0          return ClientPagedResultList(self.provider,
    96         2         41.0     20.5      0.0                                       matches if matches else [])

Total time: 0.527011 s
Function: delete at line 333

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   333                                               @dispatch(event="provider.security.key_pairs.delete",
   334                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   335                                               @profile
   336                                               def delete(self, key_pair):
   337         3          4.0      1.3      0.0          key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
   338         1     128431.0 128431.0     24.4                      self.get(key_pair))
   339         3          1.0      0.3      0.0          if key_pair:
   340                                                       # pylint:disable=protected-access
   341         3     398575.0 132858.3     75.6              self.provider.azure_client.delete_public_key(key_pair._key_pair)

Total time: 0.263378 s
Function: find at line 289

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   289                                               @dispatch(event="provider.security.key_pairs.find",
   290                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   291                                               @profile
   292                                               def find(self, **kwargs):
   293         3          4.0      1.3      0.0          obj_list = self
   294         3          2.0      0.7      0.0          filters = ['name']
   295         3     263278.0  87759.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   296                                           
   297                                                   # All kwargs should have been popped at this time.
   298         2          2.0      1.0      0.0          if len(kwargs) > 0:
   299                                                       raise InvalidParamException(
   300                                                           "Unrecognised parameters for search: %s. Supported "
   301                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   302                                           
   303         2          9.0      4.5      0.0          return ClientPagedResultList(self.provider,
   304         2         83.0     41.5      0.0                                       matches if matches else [])

Total time: 0.177344 s
Function: refresh at line 105

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   105                                               @profile
   106                                               def refresh(self):
   107                                                   """
   108                                                   Refreshes the security group with tags if required.
   109                                                   """
   110         1          1.0      1.0      0.0          try:
   111         1          9.0      9.0      0.0              self._vm_firewall = self._provider.azure_client. \
   112         1     177332.0 177332.0    100.0                  get_vm_firewall(self.id)
   113         1          2.0      2.0      0.0              if not self._vm_firewall.tags:
   114                                                           self._vm_firewall.tags = {}
   115                                                   except (CloudError, ValueError) as cloud_error:
   116                                                       log.exception(cloud_error.message)

Total time: 0.0011 s
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125         3          7.0      2.3      0.6          obj_list = firewall.rules
   126         3          3.0      1.0      0.3          filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127         3          2.0      0.7      0.2                     'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128         3       1047.0    349.0     95.2          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129         2         41.0     20.5      3.7          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.001076 s
Function: list at line 173

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   173                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   174                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   175                                               @profile
   176                                               def list(self, firewall, limit=None, marker=None):
   177                                                   # Filter out firewall rules with priority < 3500 because values
   178                                                   # between 3500 and 4096 are assumed to be owned by cloudbridge
   179                                                   # default rules.
   180                                                   # pylint:disable=protected-access
   181        15         19.0      1.3      1.8          rules = [AzureVMFirewallRule(firewall, rule) for rule
   182        15        661.0     44.1     61.4                   in firewall._vm_firewall.security_rules
   183                                                            if rule.priority < 3500]
   184        15         32.0      2.1      3.0          return ClientPagedResultList(self.provider, rules,
   185        15        364.0     24.3     33.8                                       limit=limit, marker=marker)

Total time: 0.000267 s
Function: get at line 111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   111                                               @dispatch(event="provider.security.vm_firewall_rules.get",
   112                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   113                                               @profile
   114                                               def get(self, firewall, rule_id):
   115         2        264.0    132.0     98.9          matches = [rule for rule in firewall.rules if rule.id == rule_id]
   116         2          2.0      1.0      0.7          if matches:
   117         1          0.0      0.0      0.0              return matches[0]
   118                                                   else:
   119         1          1.0      1.0      0.4              return None

