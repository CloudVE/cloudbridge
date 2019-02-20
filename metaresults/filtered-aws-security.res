cloudbridge.test.test_security_service.CloudSecurityServiceTestCase


Test output
 ..........
----------------------------------------------------------------------
Ran 10 tests in 19.266s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 3.06949 s
Function: create at line 186

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   186                                               @cb_helpers.deprecated_alias(network_id='network')
   187                                               @dispatch(event="provider.security.vm_firewalls.create",
   188                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   189                                               @profile
   190                                               def create(self, label, network, description=None):
   191        16        258.0     16.1      0.0          AWSVMFirewall.assert_valid_resource_label(label)
   192         6        306.0     51.0      0.0          name = AWSVMFirewall._generate_name_from_label(label, 'cb-fw')
   193         6         11.0      1.8      0.0          network_id = network.id if isinstance(network, Network) else network
   194         6         21.0      3.5      0.0          obj = self.svc.create('create_security_group', GroupName=name,
   195         6          1.0      0.2      0.0                                Description=name,
   196         6     738757.0 123126.2     24.1                                VpcId=network_id)
   197         6    1024069.0 170678.2     33.4          obj.label = label
   198         6    1306055.0 217675.8     42.5          obj.description = description
   199         6          9.0      1.5      0.0          return obj

Total time: 2.39902 s
Function: list at line 180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   180                                               @dispatch(event="provider.security.vm_firewalls.list",
   181                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   182                                               @profile
   183                                               def list(self, limit=None, marker=None):
   184        23    2399023.0 104305.3    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 2.00376 s
Function: create at line 248

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   248                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   249                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   250                                               @profile
   251                                               def create(self, firewall,  direction, protocol=None, from_port=None,
   252                                                          to_port=None, cidr=None, src_dest_fw=None):
   253                                                   src_dest_fw_id = (
   254         5         19.0      3.8      0.0              src_dest_fw.id if isinstance(src_dest_fw, AWSVMFirewall)
   255         4          3.0      0.8      0.0              else src_dest_fw)
   256                                           
   257                                                   # pylint:disable=protected-access
   258         5          9.0      1.8      0.0          ip_perm_entry = AWSVMFirewallRule._construct_ip_perms(
   259         5         18.0      3.6      0.0              protocol, from_port, to_port, cidr, src_dest_fw_id)
   260                                                   # Filter out empty values to please Boto
   261         5         77.0     15.4      0.0          ip_perms = [trim_empty_params(ip_perm_entry)]
   262                                           
   263         5          1.0      0.2      0.0          try:
   264         5          9.0      1.8      0.0              if direction == TrafficDirection.INBOUND:
   265                                                           # pylint:disable=protected-access
   266         5          5.0      1.0      0.0                  firewall._vm_firewall.authorize_ingress(
   267         5    1321525.0 264305.0     66.0                      IpPermissions=ip_perms)
   268                                                       elif direction == TrafficDirection.OUTBOUND:
   269                                                           # pylint:disable=protected-access
   270                                                           firewall._vm_firewall.authorize_egress(
   271                                                               IpPermissions=ip_perms)
   272                                                       else:
   273                                                           raise InvalidValueException("direction", direction)
   274         4     681808.0 170452.0     34.0              firewall.refresh()
   275         4        212.0     53.0      0.0              return AWSVMFirewallRule(firewall, direction, ip_perm_entry)
   276         1          3.0      3.0      0.0          except ClientError as ec2e:
   277         1          2.0      2.0      0.0              if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
   278         1          0.0      0.0      0.0                  return AWSVMFirewallRule(
   279         1         71.0     71.0      0.0                      firewall, direction, ip_perm_entry)
   280                                                       else:
   281                                                           raise ec2e

Total time: 1.54118 s
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105         6         19.0      3.2      0.0          zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
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
  1130         6    1540954.0 256825.7    100.0          snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132         6         13.0      2.2      0.0          if snl:
  1133                                                       # pylint:disable=protected-access
  1134         6         75.0     12.5      0.0              snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135         6          6.0      1.0      0.0              if not zone_name:
  1136                                                           return snl[0]
  1137         6          9.0      1.5      0.0              for subnet in snl:
  1138         6        100.0     16.7      0.0                  if subnet.zone.name == zone_name:
  1139         6          6.0      1.0      0.0                      return subnet
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

Total time: 1.54059 s
Function: delete at line 216

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   216                                               @dispatch(event="provider.security.vm_firewalls.delete",
   217                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   218                                               @profile
   219                                               def delete(self, vm_firewall):
   220         6          9.0      1.5      0.0          firewall = (vm_firewall if isinstance(vm_firewall, AWSVMFirewall)
   221                                                               else self.get(vm_firewall))
   222         6          5.0      0.8      0.0          if firewall:
   223                                                       # pylint:disable=protected-access
   224         6    1540573.0 256762.2    100.0              firewall._vm_firewall.delete()

Total time: 1.47682 s
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065         6         16.0      2.7      0.0          label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068         6          7.0      1.2      0.0          if len(kwargs) > 0:
  1069                                                       raise InvalidParamException(
  1070                                                           "Unrecognised parameters for search: %s. Supported "
  1071                                                           "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073         6         72.0     12.0      0.0          log.debug("Searching for AWS Subnet Service %s", label)
  1074         6    1476721.0 246120.2    100.0          return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 1.37521 s
Function: label at line 640

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   640                                               @label.setter
   641                                               # pylint:disable=arguments-differ
   642                                               @profile
   643                                               def label(self, value):
   644        17        215.0     12.6      0.0          self.assert_valid_resource_label(value)
   645         9         13.0      1.4      0.0          self._vm_firewall.create_tags(Tags=[{'Key': 'Name',
   646         9    1374985.0 152776.1    100.0                                               'Value': value or ""}])

Total time: 1.30596 s
Function: description at line 655

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   655                                               @description.setter
   656                                               # pylint:disable=arguments-differ
   657                                               @profile
   658                                               def description(self, value):
   659         6          7.0      1.2      0.0          self._vm_firewall.create_tags(Tags=[{'Key': 'Description',
   660         6    1305949.0 217658.2    100.0                                               'Value': value or ""}])

Total time: 1.25366 s
Function: refresh at line 670

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   670                                               @profile
   671                                               def refresh(self):
   672         8    1253658.0 156707.2    100.0          self._vm_firewall.reload()

Total time: 1.13273 s
Function: delete at line 283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   283                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   284                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   285                                               @profile
   286                                               def delete(self, firewall, rule):
   287                                                   # pylint:disable=protected-access
   288         3          9.0      3.0      0.0          ip_perm_entry = rule._construct_ip_perms(
   289         3         17.0      5.7      0.0              rule.protocol, rule.from_port, rule.to_port,
   290         3         25.0      8.3      0.0              rule.cidr, rule.src_dest_fw_id)
   291                                           
   292                                                   # Filter out empty values to please Boto
   293         3         54.0     18.0      0.0          ip_perms = [trim_empty_params(ip_perm_entry)]
   294                                           
   295                                                   # pylint:disable=protected-access
   296         3         16.0      5.3      0.0          if rule.direction == TrafficDirection.INBOUND:
   297         2          5.0      2.5      0.0              firewall._vm_firewall.revoke_ingress(
   298         2     504969.0 252484.5     44.6                  IpPermissions=ip_perms)
   299                                                   else:
   300                                                       # pylint:disable=protected-access
   301         1          2.0      2.0      0.0              firewall._vm_firewall.revoke_egress(
   302         1     127814.0 127814.0     11.3                  IpPermissions=ip_perms)
   303         3     499821.0 166607.0     44.1          firewall.refresh()

Total time: 0.82054 s
Function: create at line 134

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   134                                               @dispatch(event="provider.security.key_pairs.create",
   135                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   136                                               @profile
   137                                               def create(self, name, public_key_material=None):
   138        14        287.0     20.5      0.0          AWSKeyPair.assert_valid_resource_name(name)
   139         4          4.0      1.0      0.0          private_key = None
   140         4          2.0      0.5      0.0          if not public_key_material:
   141         3     135381.0  45127.0     16.5              public_key_material, private_key = cb_helpers.generate_key_pair()
   142         4          6.0      1.5      0.0          try:
   143         4         17.0      4.2      0.0              kp = self.svc.create('import_key_pair', KeyName=name,
   144         4     684822.0 171205.5     83.5                                   PublicKeyMaterial=public_key_material)
   145         3         13.0      4.3      0.0              kp.material = private_key
   146         3          1.0      0.3      0.0              return kp
   147         1          2.0      2.0      0.0          except ClientError as e:
   148         1          2.0      2.0      0.0              if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
   149         1          1.0      1.0      0.0                  raise DuplicateResourceException(
   150         1          2.0      2.0      0.0                      'Keypair already exists with name {0}'.format(name))
   151                                                       else:
   152                                                           raise e

Total time: 0.737689 s
Function: find at line 201

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   201                                               @dispatch(event="provider.security.vm_firewalls.find",
   202                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   203                                               @profile
   204                                               def find(self, **kwargs):
   205                                                   # Filter by name or label
   206         3          6.0      2.0      0.0          label = kwargs.pop('label', None)
   207         3         21.0      7.0      0.0          log.debug("Searching for Firewall Service %s", label)
   208                                                   # All kwargs should have been popped at this time.
   209         3          3.0      1.0      0.0          if len(kwargs) > 0:
   210         1          1.0      1.0      0.0              raise InvalidParamException(
   211         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   212         1         12.0     12.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   213         2          3.0      1.5      0.0          return self.svc.find(filter_name='tag:Name',
   214         2     737642.0 368821.0    100.0                               filter_value=label)

Total time: 0.567762 s
Function: get at line 963

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   963                                               @dispatch(event="provider.networking.networks.get",
   964                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   965                                               @profile
   966                                               def get(self, network_id):
   967         6     567762.0  94627.0    100.0          return self.svc.get(network_id)

Total time: 0.539951 s
Function: delete at line 154

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   154                                               @dispatch(event="provider.security.key_pairs.delete",
   155                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   156                                               @profile
   157                                               def delete(self, key_pair):
   158         3          9.0      3.0      0.0          key_pair = (key_pair if isinstance(key_pair, AWSKeyPair) else
   159         1     149089.0 149089.0     27.6                      self.get(key_pair))
   160         3          3.0      1.0      0.0          if key_pair:
   161                                                       # pylint:disable=protected-access
   162         3     390850.0 130283.3     72.4              key_pair._key_pair.delete()

Total time: 0.40985 s
Function: list at line 113

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   113                                               @dispatch(event="provider.security.key_pairs.list",
   114                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   115                                               @profile
   116                                               def list(self, limit=None, marker=None):
   117         5     409850.0  81970.0    100.0          return self.svc.list(limit=limit, marker=marker)

Total time: 0.367371 s
Function: get at line 106

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   106                                               @dispatch(event="provider.security.key_pairs.get",
   107                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   108                                               @profile
   109                                               def get(self, key_pair_id):
   110         4         30.0      7.5      0.0          log.debug("Getting Key Pair Service %s", key_pair_id)
   111         4     367341.0  91835.2    100.0          return self.svc.get(key_pair_id)

Total time: 0.16969 s
Function: find at line 119

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   119                                               @dispatch(event="provider.security.key_pairs.find",
   120                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   121                                               @profile
   122                                               def find(self, **kwargs):
   123         3          7.0      2.3      0.0          name = kwargs.pop('name', None)
   124                                           
   125                                                   # All kwargs should have been popped at this time.
   126         3          5.0      1.7      0.0          if len(kwargs) > 0:
   127         1          1.0      1.0      0.0              raise InvalidParamException(
   128         1          0.0      0.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   129         1         13.0     13.0      0.0                  "attributes: %s" % (kwargs, 'name'))
   130                                           
   131         2         18.0      9.0      0.0          log.debug("Searching for Key Pair %s", name)
   132         2     169646.0  84823.0    100.0          return self.svc.find(filter_name='key-name', filter_value=name)

Total time: 0.15349 s
Function: get at line 173

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   173                                               @dispatch(event="provider.security.vm_firewalls.get",
   174                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   175                                               @profile
   176                                               def get(self, vm_firewall_id):
   177         3         27.0      9.0      0.0          log.debug("Getting Firewall Service with the id: %s", vm_firewall_id)
   178         3     153463.0  51154.3    100.0          return self.svc.get(vm_firewall_id)

Total time: 0.00508 s
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125         3         16.0      5.3      0.3          obj_list = firewall.rules
   126         3          3.0      1.0      0.1          filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127         3          3.0      1.0      0.1                     'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128         3       4944.0   1648.0     97.3          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129         2        114.0     57.0      2.2          return ClientPagedResultList(self._provider, list(matches))

Total time: 0.001723 s
Function: list at line 232

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   232                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   233                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   234                                               @profile
   235                                               def list(self, firewall, limit=None, marker=None):
   236                                                   # pylint:disable=protected-access
   237        15         36.0      2.4      2.1          rules = [AWSVMFirewallRule(firewall,
   238                                                                              TrafficDirection.INBOUND, r)
   239        15        584.0     38.9     33.9                   for r in firewall._vm_firewall.ip_permissions]
   240                                                   # pylint:disable=protected-access
   241        15         16.0      1.1      0.9          rules = rules + [
   242        15         16.0      1.1      0.9              AWSVMFirewallRule(
   243                                                           firewall, TrafficDirection.OUTBOUND, r)
   244        15        540.0     36.0     31.3              for r in firewall._vm_firewall.ip_permissions_egress]
   245        15         39.0      2.6      2.3          return ClientPagedResultList(self.provider, rules,
   246        15        492.0     32.8     28.6                                       limit=limit, marker=marker)

Total time: 0.000372 s
Function: get at line 111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   111                                               @dispatch(event="provider.security.vm_firewall_rules.get",
   112                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   113                                               @profile
   114                                               def get(self, firewall, rule_id):
   115         2        369.0    184.5     99.2          matches = [rule for rule in firewall.rules if rule.id == rule_id]
   116         2          1.0      0.5      0.3          if matches:
   117         1          1.0      1.0      0.3              return matches[0]
   118                                                   else:
   119         1          1.0      1.0      0.3              return None

