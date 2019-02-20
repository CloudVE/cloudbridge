cloudbridge.test.test_object_life_cycle.CloudObjectLifeCycleTestCase


Test output
 .
----------------------------------------------------------------------
Ran 1 test in 5.859s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @dispatch(event="provider.security.vm_firewalls.find",
    82                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
    83                                               @profile
    84                                               def find(self, **kwargs):
    85                                                   obj_list = self
    86                                                   filters = ['label']
    87                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
    88                                           
    89                                                   # All kwargs should have been popped at this time.
    90                                                   if len(kwargs) > 0:
    91                                                       raise InvalidParamException(
    92                                                           "Unrecognised parameters for search: %s. Supported "
    93                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
    94                                           
    95                                                   return ClientPagedResultList(self.provider,
    96                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: get at line 111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   111                                               @dispatch(event="provider.security.vm_firewall_rules.get",
   112                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   113                                               @profile
   114                                               def get(self, firewall, rule_id):
   115                                                   matches = [rule for rule in firewall.rules if rule.id == rule_id]
   116                                                   if matches:
   117                                                       return matches[0]
   118                                                   else:
   119                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 121

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   121                                               @dispatch(event="provider.security.vm_firewall_rules.find",
   122                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   123                                               @profile
   124                                               def find(self, firewall, **kwargs):
   125                                                   obj_list = firewall.rules
   126                                                   filters = ['name', 'direction', 'protocol', 'from_port', 'to_port',
   127                                                              'cidr', 'src_dest_fw', 'src_dest_fw_id']
   128                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   129                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 163

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   163                                               @dispatch(event="provider.storage.buckets.find",
   164                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   165                                               @profile
   166                                               def find(self, **kwargs):
   167                                                   obj_list = self
   168                                                   filters = ['name']
   169                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   170                                           
   171                                                   # All kwargs should have been popped at this time.
   172                                                   if len(kwargs) > 0:
   173                                                       raise InvalidParamException(
   174                                                           "Unrecognised parameters for search: %s. Supported "
   175                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   176                                           
   177                                                   return ClientPagedResultList(self.provider,
   178                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222                                                   vm_type = (t for t in self if t.id == vm_type_id)
   223                                                   return next(vm_type, None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229                                                   obj_list = self
   230                                                   filters = ['name']
   231                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 242

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   242                                               @dispatch(event="provider.compute.regions.find",
   243                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   244                                               @profile
   245                                               def find(self, **kwargs):
   246                                                   obj_list = self
   247                                                   filters = ['name']
   248                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   249                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: get_or_create_default at line 270

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   270                                               @profile
   271                                               def get_or_create_default(self):
   272                                                   networks = self.provider.networking.networks.find(
   273                                                       label=BaseNetwork.CB_DEFAULT_NETWORK_LABEL)
   274                                           
   275                                                   if networks:
   276                                                       return networks[0]
   277                                                   else:
   278                                                       log.info("Creating a CloudBridge-default network labeled %s",
   279                                                                BaseNetwork.CB_DEFAULT_NETWORK_LABEL)
   280                                                       return self.provider.networking.networks.create(
   281                                                           BaseNetwork.CB_DEFAULT_NETWORK_LABEL, '10.0.0.0/16')

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   283                                               @dispatch(event="provider.networking.networks.find",
   284                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   285                                               @profile
   286                                               def find(self, **kwargs):
   287                                                   obj_list = self
   288                                                   filters = ['label']
   289                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   290                                           
   291                                                   # All kwargs should have been popped at this time.
   292                                                   if len(kwargs) > 0:
   293                                                       raise TypeError("Unrecognised parameters for search: %s."
   294                                                                       " Supported attributes: %s" % (kwargs,
   295                                                                                                      ", ".join(filters)))
   296                                           
   297                                                   return ClientPagedResultList(self.provider,
   298                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312                                                   if not network:
   313                                                       obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316                                                   filters = ['label']
   317                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323                                                   matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324                                                   if matches:
   325                                                       return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: get_or_create_default at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @profile
   342                                               def get_or_create_default(self, network):
   343                                                   net_id = network.id if isinstance(network, Network) else network
   344                                                   routers = self.provider.networking.routers.find(
   345                                                       label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)
   346                                                   for router in routers:
   347                                                       if router.network_id == net_id:
   348                                                           return router
   349                                                   else:
   350                                                       return self.provider.networking.routers.create(
   351                                                           network=net_id, label=BaseRouter.CB_DEFAULT_ROUTER_LABEL)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/services.py
Function: find at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.networking.floating_ips.find",
   376                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def find(self, gateway, **kwargs):
   379                                                   obj_list = gateway.floating_ips
   380                                                   filters = ['name', 'public_ip']
   381                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   382                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 88

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    88                                               @label.setter
    89                                               # pylint:disable=arguments-differ
    90                                               @profile
    91                                               def label(self, value):
    92                                                   self.assert_valid_resource_label(value)
    93                                                   self._ec2_image.create_tags(Tags=[{'Key': 'Name',
    94                                                                                      'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 134

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   134                                               @profile
   135                                               def refresh(self):
   136                                                   self._ec2_image.reload()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @label.setter
   255                                               # pylint:disable=arguments-differ
   256                                               @profile
   257                                               def label(self, value):
   258                                                   self.assert_valid_resource_label(value)
   259                                                   self._ec2_instance.create_tags(Tags=[{'Key': 'Name',
   260                                                                                         'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 376

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   376                                               @profile
   377                                               def refresh(self):
   378                                                   try:
   379                                                       self._ec2_instance.reload()
   380                                                       self._unknown_state = False
   381                                                   except ClientError:
   382                                                       # The instance no longer exists and cannot be refreshed.
   383                                                       # set the state to unknown
   384                                                       self._unknown_state = True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 426

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   426                                               @label.setter
   427                                               # pylint:disable=arguments-differ
   428                                               @profile
   429                                               def label(self, value):
   430                                                   self.assert_valid_resource_label(value)
   431                                                   self._volume.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: description at line 437

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   437                                               @description.setter
   438                                               @profile
   439                                               def description(self, value):
   440                                                   self._volume.create_tags(Tags=[{'Key': 'Description',
   441                                                                                   'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 509

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   509                                               @profile
   510                                               def refresh(self):
   511                                                   try:
   512                                                       self._volume.reload()
   513                                                       self._unknown_state = False
   514                                                   except ClientError:
   515                                                       # The volume no longer exists and cannot be refreshed.
   516                                                       # set the status to unknown
   517                                                       self._unknown_state = True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 552

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   552                                               @label.setter
   553                                               # pylint:disable=arguments-differ
   554                                               @profile
   555                                               def label(self, value):
   556                                                   self.assert_valid_resource_label(value)
   557                                                   self._snapshot.create_tags(Tags=[{'Key': 'Name',
   558                                                                                     'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: description at line 564

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   564                                               @description.setter
   565                                               @profile
   566                                               def description(self, value):
   567                                                   self._snapshot.create_tags(Tags=[{
   568                                                       'Key': 'Description', 'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 593

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   593                                               @profile
   594                                               def refresh(self):
   595                                                   try:
   596                                                       self._snapshot.reload()
   597                                                       self._unknown_state = False
   598                                                   except ClientError:
   599                                                       # The snapshot no longer exists and cannot be refreshed.
   600                                                       # set the status to unknown
   601                                                       self._unknown_state = True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 640

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   640                                               @label.setter
   641                                               # pylint:disable=arguments-differ
   642                                               @profile
   643                                               def label(self, value):
   644                                                   self.assert_valid_resource_label(value)
   645                                                   self._vm_firewall.create_tags(Tags=[{'Key': 'Name',
   646                                                                                        'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: description at line 655

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   655                                               @description.setter
   656                                               # pylint:disable=arguments-differ
   657                                               @profile
   658                                               def description(self, value):
   659                                                   self._vm_firewall.create_tags(Tags=[{'Key': 'Description',
   660                                                                                        'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 670

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   670                                               @profile
   671                                               def refresh(self):
   672                                                   self._vm_firewall.reload()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 814

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   814                                               @profile
   815                                               def refresh(self):
   816                                                   self._obj.load()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @label.setter
   897                                               # pylint:disable=arguments-differ
   898                                               @profile
   899                                               def label(self, value):
   900                                                   self.assert_valid_resource_label(value)
   901                                                   self._vpc.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 930

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   930                                               @profile
   931                                               def refresh(self):
   932                                                   try:
   933                                                       self._vpc.reload()
   934                                                       self._unknown_state = False
   935                                                   except ClientError:
   936                                                       # The network no longer exists and cannot be refreshed.
   937                                                       # set the status to unknown
   938                                                       self._unknown_state = True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 975

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   975                                               @label.setter
   976                                               # pylint:disable=arguments-differ
   977                                               @profile
   978                                               def label(self, value):
   979                                                   self.assert_valid_resource_label(value)
   980                                                   self._subnet.create_tags(Tags=[{'Key': 'Name', 'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 1006

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1006                                               @profile
  1007                                               def refresh(self):
  1008                                                   try:
  1009                                                       self._subnet.reload()
  1010                                                       self._unknown_state = False
  1011                                                   except ClientError:
  1012                                                       # subnet no longer exists
  1013                                                       self._unknown_state = True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 1038

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1038                                               @profile
  1039                                               def refresh(self):
  1040                                                   self._ip.reload()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: label at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @label.setter
  1062                                               # pylint:disable=arguments-differ
  1063                                               @profile
  1064                                               def label(self, value):
  1065                                                   self.assert_valid_resource_label(value)
  1066                                                   self._route_table.create_tags(Tags=[{'Key': 'Name',
  1067                                                                                        'Value': value or ""}])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 1069

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1069                                               @profile
  1070                                               def refresh(self):
  1071                                                   try:
  1072                                                       self._route_table.reload()
  1073                                                   except ClientError:
  1074                                                       self._route_table.associations = None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/resources.py
Function: refresh at line 1135

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1135                                               @profile
  1136                                               def refresh(self):
  1137                                                   try:
  1138                                                       self._gateway.reload()
  1139                                                   except ClientError:
  1140                                                       self._gateway.state = GatewayState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 106

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   106                                               @dispatch(event="provider.security.key_pairs.get",
   107                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   108                                               @profile
   109                                               def get(self, key_pair_id):
   110                                                   log.debug("Getting Key Pair Service %s", key_pair_id)
   111                                                   return self.svc.get(key_pair_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 113

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   113                                               @dispatch(event="provider.security.key_pairs.list",
   114                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   115                                               @profile
   116                                               def list(self, limit=None, marker=None):
   117                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 119

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   119                                               @dispatch(event="provider.security.key_pairs.find",
   120                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   121                                               @profile
   122                                               def find(self, **kwargs):
   123                                                   name = kwargs.pop('name', None)
   124                                           
   125                                                   # All kwargs should have been popped at this time.
   126                                                   if len(kwargs) > 0:
   127                                                       raise InvalidParamException(
   128                                                           "Unrecognised parameters for search: %s. Supported "
   129                                                           "attributes: %s" % (kwargs, 'name'))
   130                                           
   131                                                   log.debug("Searching for Key Pair %s", name)
   132                                                   return self.svc.find(filter_name='key-name', filter_value=name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 134

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   134                                               @dispatch(event="provider.security.key_pairs.create",
   135                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   136                                               @profile
   137                                               def create(self, name, public_key_material=None):
   138                                                   AWSKeyPair.assert_valid_resource_name(name)
   139                                                   private_key = None
   140                                                   if not public_key_material:
   141                                                       public_key_material, private_key = cb_helpers.generate_key_pair()
   142                                                   try:
   143                                                       kp = self.svc.create('import_key_pair', KeyName=name,
   144                                                                            PublicKeyMaterial=public_key_material)
   145                                                       kp.material = private_key
   146                                                       return kp
   147                                                   except ClientError as e:
   148                                                       if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
   149                                                           raise DuplicateResourceException(
   150                                                               'Keypair already exists with name {0}'.format(name))
   151                                                       else:
   152                                                           raise e

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 154

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   154                                               @dispatch(event="provider.security.key_pairs.delete",
   155                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   156                                               @profile
   157                                               def delete(self, key_pair):
   158                                                   key_pair = (key_pair if isinstance(key_pair, AWSKeyPair) else
   159                                                               self.get(key_pair))
   160                                                   if key_pair:
   161                                                       # pylint:disable=protected-access
   162                                                       key_pair._key_pair.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 173

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   173                                               @dispatch(event="provider.security.vm_firewalls.get",
   174                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   175                                               @profile
   176                                               def get(self, vm_firewall_id):
   177                                                   log.debug("Getting Firewall Service with the id: %s", vm_firewall_id)
   178                                                   return self.svc.get(vm_firewall_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   180                                               @dispatch(event="provider.security.vm_firewalls.list",
   181                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   182                                               @profile
   183                                               def list(self, limit=None, marker=None):
   184                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 186

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   186                                               @cb_helpers.deprecated_alias(network_id='network')
   187                                               @dispatch(event="provider.security.vm_firewalls.create",
   188                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   189                                               @profile
   190                                               def create(self, label, network, description=None):
   191                                                   AWSVMFirewall.assert_valid_resource_label(label)
   192                                                   name = AWSVMFirewall._generate_name_from_label(label, 'cb-fw')
   193                                                   network_id = network.id if isinstance(network, Network) else network
   194                                                   obj = self.svc.create('create_security_group', GroupName=name,
   195                                                                         Description=name,
   196                                                                         VpcId=network_id)
   197                                                   obj.label = label
   198                                                   obj.description = description
   199                                                   return obj

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 201

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   201                                               @dispatch(event="provider.security.vm_firewalls.find",
   202                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   203                                               @profile
   204                                               def find(self, **kwargs):
   205                                                   # Filter by name or label
   206                                                   label = kwargs.pop('label', None)
   207                                                   log.debug("Searching for Firewall Service %s", label)
   208                                                   # All kwargs should have been popped at this time.
   209                                                   if len(kwargs) > 0:
   210                                                       raise InvalidParamException(
   211                                                           "Unrecognised parameters for search: %s. Supported "
   212                                                           "attributes: %s" % (kwargs, 'label'))
   213                                                   return self.svc.find(filter_name='tag:Name',
   214                                                                        filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 216

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   216                                               @dispatch(event="provider.security.vm_firewalls.delete",
   217                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   218                                               @profile
   219                                               def delete(self, vm_firewall):
   220                                                   firewall = (vm_firewall if isinstance(vm_firewall, AWSVMFirewall)
   221                                                               else self.get(vm_firewall))
   222                                                   if firewall:
   223                                                       # pylint:disable=protected-access
   224                                                       firewall._vm_firewall.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 232

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   232                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   233                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   234                                               @profile
   235                                               def list(self, firewall, limit=None, marker=None):
   236                                                   # pylint:disable=protected-access
   237                                                   rules = [AWSVMFirewallRule(firewall,
   238                                                                              TrafficDirection.INBOUND, r)
   239                                                            for r in firewall._vm_firewall.ip_permissions]
   240                                                   # pylint:disable=protected-access
   241                                                   rules = rules + [
   242                                                       AWSVMFirewallRule(
   243                                                           firewall, TrafficDirection.OUTBOUND, r)
   244                                                       for r in firewall._vm_firewall.ip_permissions_egress]
   245                                                   return ClientPagedResultList(self.provider, rules,
   246                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 248

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   248                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   249                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   250                                               @profile
   251                                               def create(self, firewall,  direction, protocol=None, from_port=None,
   252                                                          to_port=None, cidr=None, src_dest_fw=None):
   253                                                   src_dest_fw_id = (
   254                                                       src_dest_fw.id if isinstance(src_dest_fw, AWSVMFirewall)
   255                                                       else src_dest_fw)
   256                                           
   257                                                   # pylint:disable=protected-access
   258                                                   ip_perm_entry = AWSVMFirewallRule._construct_ip_perms(
   259                                                       protocol, from_port, to_port, cidr, src_dest_fw_id)
   260                                                   # Filter out empty values to please Boto
   261                                                   ip_perms = [trim_empty_params(ip_perm_entry)]
   262                                           
   263                                                   try:
   264                                                       if direction == TrafficDirection.INBOUND:
   265                                                           # pylint:disable=protected-access
   266                                                           firewall._vm_firewall.authorize_ingress(
   267                                                               IpPermissions=ip_perms)
   268                                                       elif direction == TrafficDirection.OUTBOUND:
   269                                                           # pylint:disable=protected-access
   270                                                           firewall._vm_firewall.authorize_egress(
   271                                                               IpPermissions=ip_perms)
   272                                                       else:
   273                                                           raise InvalidValueException("direction", direction)
   274                                                       firewall.refresh()
   275                                                       return AWSVMFirewallRule(firewall, direction, ip_perm_entry)
   276                                                   except ClientError as ec2e:
   277                                                       if ec2e.response['Error']['Code'] == "InvalidPermission.Duplicate":
   278                                                           return AWSVMFirewallRule(
   279                                                               firewall, direction, ip_perm_entry)
   280                                                       else:
   281                                                           raise ec2e

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   283                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   284                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   285                                               @profile
   286                                               def delete(self, firewall, rule):
   287                                                   # pylint:disable=protected-access
   288                                                   ip_perm_entry = rule._construct_ip_perms(
   289                                                       rule.protocol, rule.from_port, rule.to_port,
   290                                                       rule.cidr, rule.src_dest_fw_id)
   291                                           
   292                                                   # Filter out empty values to please Boto
   293                                                   ip_perms = [trim_empty_params(ip_perm_entry)]
   294                                           
   295                                                   # pylint:disable=protected-access
   296                                                   if rule.direction == TrafficDirection.INBOUND:
   297                                                       firewall._vm_firewall.revoke_ingress(
   298                                                           IpPermissions=ip_perms)
   299                                                   else:
   300                                                       # pylint:disable=protected-access
   301                                                       firewall._vm_firewall.revoke_egress(
   302                                                           IpPermissions=ip_perms)
   303                                                   firewall.refresh()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 342

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   342                                               @dispatch(event="provider.storage.volumes.get",
   343                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   344                                               @profile
   345                                               def get(self, volume_id):
   346                                                   return self.svc.get(volume_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 348

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   348                                               @dispatch(event="provider.storage.volumes.find",
   349                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   350                                               @profile
   351                                               def find(self, **kwargs):
   352                                                   label = kwargs.pop('label', None)
   353                                           
   354                                                   # All kwargs should have been popped at this time.
   355                                                   if len(kwargs) > 0:
   356                                                       raise InvalidParamException(
   357                                                           "Unrecognised parameters for search: %s. Supported "
   358                                                           "attributes: %s" % (kwargs, 'label'))
   359                                           
   360                                                   log.debug("Searching for AWS Volume Service %s", label)
   361                                                   return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 363

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   363                                               @dispatch(event="provider.storage.volumes.list",
   364                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   365                                               @profile
   366                                               def list(self, limit=None, marker=None):
   367                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   369                                               @dispatch(event="provider.storage.volumes.create",
   370                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   371                                               @profile
   372                                               def create(self, label, size, zone, snapshot=None, description=None):
   373                                                   AWSVolume.assert_valid_resource_label(label)
   374                                                   zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   375                                                   snapshot_id = snapshot.id if isinstance(
   376                                                       snapshot, AWSSnapshot) and snapshot else snapshot
   377                                           
   378                                                   cb_vol = self.svc.create('create_volume', Size=size,
   379                                                                            AvailabilityZone=zone_id,
   380                                                                            SnapshotId=snapshot_id)
   381                                                   # Wait until ready to tag instance
   382                                                   cb_vol.wait_till_ready()
   383                                                   cb_vol.label = label
   384                                                   if description:
   385                                                       cb_vol.description = description
   386                                                   return cb_vol

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 388

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   388                                               @dispatch(event="provider.storage.volumes.delete",
   389                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   390                                               @profile
   391                                               def delete(self, vol):
   392                                                   volume = vol if isinstance(vol, AWSVolume) else self.get(vol)
   393                                                   if volume:
   394                                                       # pylint:disable=protected-access
   395                                                       volume._volume.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 406

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   406                                               @dispatch(event="provider.storage.snapshots.get",
   407                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   408                                               @profile
   409                                               def get(self, snapshot_id):
   410                                                   return self.svc.get(snapshot_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 412

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   412                                               @dispatch(event="provider.storage.snapshots.find",
   413                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   414                                               @profile
   415                                               def find(self, **kwargs):
   416                                                   # Filter by description or label
   417                                                   label = kwargs.get('label', None)
   418                                           
   419                                                   obj_list = []
   420                                                   if label:
   421                                                       log.debug("Searching for AWS Snapshot with label %s", label)
   422                                                       obj_list.extend(self.svc.find(filter_name='tag:Name',
   423                                                                                     filter_value=label,
   424                                                                                     OwnerIds=['self']))
   425                                                   else:
   426                                                       obj_list = list(self)
   427                                                   filters = ['label']
   428                                                   return cb_helpers.generic_find(filters, kwargs, obj_list)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   430                                               @dispatch(event="provider.storage.snapshots.list",
   431                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   432                                               @profile
   433                                               def list(self, limit=None, marker=None):
   434                                                   return self.svc.list(limit=limit, marker=marker,
   435                                                                        OwnerIds=['self'])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 437

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   437                                               @dispatch(event="provider.storage.snapshots.create",
   438                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   439                                               @profile
   440                                               def create(self, label, volume, description=None):
   441                                                   AWSSnapshot.assert_valid_resource_label(label)
   442                                                   volume_id = volume.id if isinstance(volume, AWSVolume) else volume
   443                                           
   444                                                   cb_snap = self.svc.create('create_snapshot', VolumeId=volume_id)
   445                                                   # Wait until ready to tag instance
   446                                                   cb_snap.wait_till_ready()
   447                                                   cb_snap.label = label
   448                                                   if cb_snap.description:
   449                                                       cb_snap.description = description
   450                                                   return cb_snap

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   452                                               @dispatch(event="provider.storage.snapshots.delete",
   453                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   454                                               @profile
   455                                               def delete(self, snapshot):
   456                                                   snapshot = (snapshot if isinstance(snapshot, AWSSnapshot) else
   457                                                               self.get(snapshot))
   458                                                   if snapshot:
   459                                                       # pylint:disable=protected-access
   460                                                       snapshot._snapshot.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 471

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   471                                               @dispatch(event="provider.storage.buckets.get",
   472                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   473                                               @profile
   474                                               def get(self, bucket_id):
   475                                                   """
   476                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   477                                                   does not exist.
   478                                                   """
   479                                                   try:
   480                                                       # Make a call to make sure the bucket exists. There's an edge case
   481                                                       # where a 403 response can occur when the bucket exists but the
   482                                                       # user simply does not have permissions to access it. See below.
   483                                                       self.provider.s3_conn.meta.client.head_bucket(Bucket=bucket_id)
   484                                                       return AWSBucket(self.provider,
   485                                                                        self.provider.s3_conn.Bucket(bucket_id))
   486                                                   except ClientError as e:
   487                                                       # If 403, it means the bucket exists, but the user does not have
   488                                                       # permissions to access the bucket. However, limited operations
   489                                                       # may be permitted (with a session token for example), so return a
   490                                                       # Bucket instance to allow further operations.
   491                                                       # http://stackoverflow.com/questions/32331456/using-boto-upload-file-to-s3-
   492                                                       # sub-folder-when-i-have-no-permissions-on-listing-fo
   493                                                       if e.response['Error']['Code'] == "403":
   494                                                           log.warning("AWS Bucket %s already exists but user doesn't "
   495                                                                       "have enough permissions to access the bucket",
   496                                                                       bucket_id)
   497                                                           return AWSBucket(self.provider,
   498                                                                            self.provider.s3_conn.Bucket(bucket_id))
   499                                                   # For all other responses, it's assumed that the bucket does not exist.
   500                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 502

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   502                                               @dispatch(event="provider.storage.buckets.list",
   503                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   504                                               @profile
   505                                               def list(self, limit=None, marker=None):
   506                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 508

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   508                                               @dispatch(event="provider.storage.buckets.create",
   509                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   510                                               @profile
   511                                               def create(self, name, location=None):
   512                                                   AWSBucket.assert_valid_resource_name(name)
   513                                                   location = location or self.provider.region_name
   514                                                   # Due to an API issue in S3, specifying us-east-1 as a
   515                                                   # LocationConstraint results in an InvalidLocationConstraint.
   516                                                   # Therefore, it must be special-cased and omitted altogether.
   517                                                   # See: https://github.com/boto/boto3/issues/125
   518                                                   # In addition, us-east-1 also behaves differently when it comes
   519                                                   # to raising duplicate resource exceptions, so perform a manual
   520                                                   # check
   521                                                   if location == 'us-east-1':
   522                                                       try:
   523                                                           # check whether bucket already exists
   524                                                           self.provider.s3_conn.meta.client.head_bucket(Bucket=name)
   525                                                       except ClientError as e:
   526                                                           if e.response['Error']['Code'] == "404":
   527                                                               # bucket doesn't exist, go ahead and create it
   528                                                               return self.svc.create('create_bucket', Bucket=name)
   529                                                       raise DuplicateResourceException(
   530                                                               'Bucket already exists with name {0}'.format(name))
   531                                                   else:
   532                                                       try:
   533                                                           return self.svc.create('create_bucket', Bucket=name,
   534                                                                                  CreateBucketConfiguration={
   535                                                                                      'LocationConstraint': location
   536                                                                                   })
   537                                                       except ClientError as e:
   538                                                           if e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
   539                                                               raise DuplicateResourceException(
   540                                                                   'Bucket already exists with name {0}'.format(name))
   541                                                           else:
   542                                                               raise

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 544

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   544                                               @dispatch(event="provider.storage.buckets.delete",
   545                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   546                                               @profile
   547                                               def delete(self, bucket):
   548                                                   b = bucket if isinstance(bucket, AWSBucket) else self.get(bucket)
   549                                                   if b:
   550                                                       # pylint:disable=protected-access
   551                                                       b._bucket.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 559

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   559                                               @profile
   560                                               def get(self, bucket, object_id):
   561                                                   try:
   562                                                       # pylint:disable=protected-access
   563                                                       obj = bucket._bucket.Object(object_id)
   564                                                       # load() throws an error if object does not exist
   565                                                       obj.load()
   566                                                       return AWSBucketObject(self.provider, obj)
   567                                                   except ClientError:
   568                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 570

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   570                                               @profile
   571                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   572                                                   if prefix:
   573                                                       # pylint:disable=protected-access
   574                                                       boto_objs = bucket._bucket.objects.filter(Prefix=prefix)
   575                                                   else:
   576                                                       # pylint:disable=protected-access
   577                                                       boto_objs = bucket._bucket.objects.all()
   578                                                   objects = [AWSBucketObject(self.provider, obj) for obj in boto_objs]
   579                                                   return ClientPagedResultList(self.provider, objects,
   580                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 582

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   582                                               @profile
   583                                               def find(self, bucket, **kwargs):
   584                                                   # pylint:disable=protected-access
   585                                                   obj_list = [AWSBucketObject(self.provider, o)
   586                                                               for o in bucket._bucket.objects.all()]
   587                                                   filters = ['name']
   588                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   589                                                   return ClientPagedResultList(self.provider, list(matches),
   590                                                                                limit=None, marker=None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 592

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   592                                               @profile
   593                                               def create(self, bucket, name):
   594                                                   # pylint:disable=protected-access
   595                                                   obj = bucket._bucket.Object(name)
   596                                                   return AWSBucketObject(self.provider, obj)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 633

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   633                                               @profile
   634                                               def get(self, image_id):
   635                                                   log.debug("Getting AWS Image Service with the id: %s", image_id)
   636                                                   return self.svc.get(image_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 638

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   638                                               @profile
   639                                               def find(self, **kwargs):
   640                                                   # Filter by name or label
   641                                                   label = kwargs.pop('label', None)
   642                                                   # Popped here, not used in the generic find
   643                                                   owner = kwargs.pop('owners', None)
   644                                           
   645                                                   # All kwargs should have been popped at this time.
   646                                                   if len(kwargs) > 0:
   647                                                       raise InvalidParamException(
   648                                                           "Unrecognised parameters for search: %s. Supported "
   649                                                           "attributes: %s" % (kwargs, 'label'))
   650                                           
   651                                                   extra_args = {}
   652                                                   if owner:
   653                                                       extra_args.update(Owners=owner)
   654                                           
   655                                                   # The original list is made by combining both searches by "tag:Name"
   656                                                   # and "AMI name" to allow for searches of public images
   657                                                   if label:
   658                                                       log.debug("Searching for AWS Image Service %s", label)
   659                                                       obj_list = []
   660                                                       obj_list.extend(self.svc.find(filter_name='name',
   661                                                                                     filter_value=label, **extra_args))
   662                                                       obj_list.extend(self.svc.find(filter_name='tag:Name',
   663                                                                                     filter_value=label, **extra_args))
   664                                                       return obj_list
   665                                                   else:
   666                                                       return []

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 668

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   668                                               @profile
   669                                               def list(self, filter_by_owner=True, limit=None, marker=None):
   670                                                   return self.svc.list(Owners=['self'] if filter_by_owner else
   671                                                                        ['amazon', 'self'],
   672                                                                        limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create_launch_config at line 765

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   765                                               @profile
   766                                               def create_launch_config(self):
   767                                                   return AWSLaunchConfig(self.provider)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 769

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   769                                               @dispatch(event="provider.compute.instances.create",
   770                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   771                                               @profile
   772                                               def create(self, label, image, vm_type, subnet, zone,
   773                                                          key_pair=None, vm_firewalls=None, user_data=None,
   774                                                          launch_config=None, **kwargs):
   775                                                   AWSInstance.assert_valid_resource_label(label)
   776                                                   image_id = image.id if isinstance(image, MachineImage) else image
   777                                                   vm_size = vm_type.id if \
   778                                                       isinstance(vm_type, VMType) else vm_type
   779                                                   subnet = (self.provider.networking.subnets.get(subnet)
   780                                                             if isinstance(subnet, str) else subnet)
   781                                                   zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   782                                                   key_pair_name = key_pair.name if isinstance(
   783                                                       key_pair,
   784                                                       KeyPair) else key_pair
   785                                                   if launch_config:
   786                                                       bdm = self._process_block_device_mappings(launch_config)
   787                                                   else:
   788                                                       bdm = None
   789                                           
   790                                                   subnet_id, zone_id, vm_firewall_ids = \
   791                                                       self._resolve_launch_options(subnet, zone_id, vm_firewalls)
   792                                           
   793                                                   placement = {'AvailabilityZone': zone_id} if zone_id else None
   794                                                   inst = self.svc.create('create_instances',
   795                                                                          ImageId=image_id,
   796                                                                          MinCount=1,
   797                                                                          MaxCount=1,
   798                                                                          KeyName=key_pair_name,
   799                                                                          SecurityGroupIds=vm_firewall_ids or None,
   800                                                                          UserData=str(user_data) or None,
   801                                                                          InstanceType=vm_size,
   802                                                                          Placement=placement,
   803                                                                          BlockDeviceMappings=bdm,
   804                                                                          SubnetId=subnet_id
   805                                                                          )
   806                                                   if inst and len(inst) == 1:
   807                                                       # Wait until the resource exists
   808                                                       # pylint:disable=protected-access
   809                                                       inst[0]._wait_till_exists()
   810                                                       # Tag the instance w/ the name
   811                                                       inst[0].label = label
   812                                                       return inst[0]
   813                                                   raise ValueError(
   814                                                       'Expected a single object response, got a list: %s' % inst)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 816

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   816                                               @dispatch(event="provider.compute.instances.get",
   817                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   818                                               @profile
   819                                               def get(self, instance_id):
   820                                                   return self.svc.get(instance_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 822

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   822                                               @dispatch(event="provider.compute.instances.find",
   823                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   824                                               @profile
   825                                               def find(self, **kwargs):
   826                                                   label = kwargs.pop('label', None)
   827                                           
   828                                                   # All kwargs should have been popped at this time.
   829                                                   if len(kwargs) > 0:
   830                                                       raise InvalidParamException(
   831                                                           "Unrecognised parameters for search: %s. Supported "
   832                                                           "attributes: %s" % (kwargs, 'label'))
   833                                           
   834                                                   return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 836

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   836                                               @dispatch(event="provider.compute.instances.list",
   837                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   838                                               @profile
   839                                               def list(self, limit=None, marker=None):
   840                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @dispatch(event="provider.compute.instances.delete",
   843                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   844                                               @profile
   845                                               def delete(self, instance):
   846                                                   aws_inst = (instance if isinstance(instance, AWSInstance) else
   847                                                               self.get(instance))
   848                                                   if aws_inst:
   849                                                       # pylint:disable=protected-access
   850                                                       aws_inst._ec2_instance.terminate()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 881

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   881                                               @dispatch(event="provider.compute.vm_types.list",
   882                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   883                                               @profile
   884                                               def list(self, limit=None, marker=None):
   885                                                   vm_types = [AWSVMType(self.provider, vm_type)
   886                                                               for vm_type in self.instance_data]
   887                                                   return ClientPagedResultList(self.provider, vm_types,
   888                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 896

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   896                                               @dispatch(event="provider.compute.regions.get",
   897                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   898                                               @profile
   899                                               def get(self, region_id):
   900                                                   log.debug("Getting AWS Region Service with the id: %s",
   901                                                             region_id)
   902                                                   region = [r for r in self if r.id == region_id]
   903                                                   if region:
   904                                                       return region[0]
   905                                                   else:
   906                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 908

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   908                                               @dispatch(event="provider.compute.regions.list",
   909                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   910                                               @profile
   911                                               def list(self, limit=None, marker=None):
   912                                                   regions = [
   913                                                       AWSRegion(self.provider, region) for region in
   914                                                       self.provider.ec2_conn.meta.client.describe_regions()
   915                                                       .get('Regions', [])]
   916                                                   return ClientPagedResultList(self.provider, regions,
   917                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 963

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   963                                               @dispatch(event="provider.networking.networks.get",
   964                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   965                                               @profile
   966                                               def get(self, network_id):
   967                                                   return self.svc.get(network_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 969

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   969                                               @dispatch(event="provider.networking.networks.list",
   970                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   971                                               @profile
   972                                               def list(self, limit=None, marker=None):
   973                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 975

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   975                                               @dispatch(event="provider.networking.networks.find",
   976                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   977                                               @profile
   978                                               def find(self, **kwargs):
   979                                                   label = kwargs.pop('label', None)
   980                                           
   981                                                   # All kwargs should have been popped at this time.
   982                                                   if len(kwargs) > 0:
   983                                                       raise InvalidParamException(
   984                                                           "Unrecognised parameters for search: %s. Supported "
   985                                                           "attributes: %s" % (kwargs, 'label'))
   986                                           
   987                                                   log.debug("Searching for AWS Network Service %s", label)
   988                                                   return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 990

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   990                                               @dispatch(event="provider.networking.networks.create",
   991                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   992                                               @profile
   993                                               def create(self, label, cidr_block):
   994                                                   AWSNetwork.assert_valid_resource_label(label)
   995                                           
   996                                                   cb_net = self.svc.create('create_vpc', CidrBlock=cidr_block)
   997                                                   # Wait until ready to tag instance
   998                                                   cb_net.wait_till_ready()
   999                                                   if label:
  1000                                                       cb_net.label = label
  1001                                                   return cb_net

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 1003

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1003                                               @dispatch(event="provider.networking.networks.delete",
  1004                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1005                                               @profile
  1006                                               def delete(self, network):
  1007                                                   network = (network if isinstance(network, AWSNetwork)
  1008                                                              else self.get(network))
  1009                                                   if network:
  1010                                                       # pylint:disable=protected-access
  1011                                                       network._vpc.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get_or_create_default at line 1013

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1013                                               @profile
  1014                                               def get_or_create_default(self):
  1015                                                   # # Look for provided default network
  1016                                                   # for net in self.provider.networking.networks:
  1017                                                   # pylint:disable=protected-access
  1018                                                   #     if net._vpc.is_default:
  1019                                                   #         return net
  1020                                           
  1021                                                   # No provider-default, try CB-default instead
  1022                                                   default_nets = self.provider.networking.networks.find(
  1023                                                       label=AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
  1024                                                   if default_nets:
  1025                                                       return default_nets[0]
  1026                                           
  1027                                                   else:
  1028                                                       log.info("Creating a CloudBridge-default network labeled %s",
  1029                                                                AWSNetwork.CB_DEFAULT_NETWORK_LABEL)
  1030                                                       return self.provider.networking.networks.create(
  1031                                                           label=AWSNetwork.CB_DEFAULT_NETWORK_LABEL,
  1032                                                           cidr_block=AWSNetwork.CB_DEFAULT_IPV4RANGE)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 1043

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1043                                               @dispatch(event="provider.networking.subnets.get",
  1044                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1045                                               @profile
  1046                                               def get(self, subnet_id):
  1047                                                   return self.svc.get(subnet_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 1049

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1049                                               @dispatch(event="provider.networking.subnets.list",
  1050                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1051                                               @profile
  1052                                               def list(self, network=None, limit=None, marker=None):
  1053                                                   network_id = network.id if isinstance(network, AWSNetwork) else network
  1054                                                   if network_id:
  1055                                                       return self.svc.find(
  1056                                                           filter_name='vpc-id', filter_value=network_id,
  1057                                                           limit=limit, marker=marker)
  1058                                                   else:
  1059                                                       return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 1061

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1061                                               @dispatch(event="provider.networking.subnets.find",
  1062                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1063                                               @profile
  1064                                               def find(self, network=None, **kwargs):
  1065                                                   label = kwargs.pop('label', None)
  1066                                           
  1067                                                   # All kwargs should have been popped at this time.
  1068                                                   if len(kwargs) > 0:
  1069                                                       raise InvalidParamException(
  1070                                                           "Unrecognised parameters for search: %s. Supported "
  1071                                                           "attributes: %s" % (kwargs, 'label'))
  1072                                           
  1073                                                   log.debug("Searching for AWS Subnet Service %s", label)
  1074                                                   return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 1076

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1076                                               @dispatch(event="provider.networking.subnets.create",
  1077                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1078                                               @profile
  1079                                               def create(self, label, network, cidr_block, zone):
  1080                                                   AWSSubnet.assert_valid_resource_label(label)
  1081                                                   zone_name = zone.name if isinstance(
  1082                                                       zone, AWSPlacementZone) else zone
  1083                                           
  1084                                                   network_id = network.id if isinstance(network, AWSNetwork) else network
  1085                                           
  1086                                                   subnet = self.svc.create('create_subnet',
  1087                                                                            VpcId=network_id,
  1088                                                                            CidrBlock=cidr_block,
  1089                                                                            AvailabilityZone=zone_name)
  1090                                                   if label:
  1091                                                       subnet.label = label
  1092                                                   return subnet

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 1094

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1094                                               @dispatch(event="provider.networking.subnets.delete",
  1095                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1096                                               @profile
  1097                                               def delete(self, subnet):
  1098                                                   sn = subnet if isinstance(subnet, AWSSubnet) else self.get(subnet)
  1099                                                   if sn:
  1100                                                       # pylint:disable=protected-access
  1101                                                       sn._subnet.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get_or_create_default at line 1103

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1103                                               @profile
  1104                                               def get_or_create_default(self, zone):
  1105                                                   zone_name = zone.name if isinstance(zone, AWSPlacementZone) else zone
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
  1130                                                   snl = self.find(label=AWSSubnet.CB_DEFAULT_SUBNET_LABEL + "*")
  1131                                           
  1132                                                   if snl:
  1133                                                       # pylint:disable=protected-access
  1134                                                       snl.sort(key=lambda sn: sn._subnet.availability_zone)
  1135                                                       if not zone_name:
  1136                                                           return snl[0]
  1137                                                       for subnet in snl:
  1138                                                           if subnet.zone.name == zone_name:
  1139                                                               return subnet
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

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 1217

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1217                                               @dispatch(event="provider.networking.routers.get",
  1218                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1219                                               @profile
  1220                                               def get(self, router_id):
  1221                                                   return self.svc.get(router_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: find at line 1223

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1223                                               @dispatch(event="provider.networking.routers.find",
  1224                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1225                                               @profile
  1226                                               def find(self, **kwargs):
  1227                                                   label = kwargs.pop('label', None)
  1228                                           
  1229                                                   # All kwargs should have been popped at this time.
  1230                                                   if len(kwargs) > 0:
  1231                                                       raise InvalidParamException(
  1232                                                           "Unrecognised parameters for search: %s. Supported "
  1233                                                           "attributes: %s" % (kwargs, 'label'))
  1234                                           
  1235                                                   log.debug("Searching for AWS Router Service %s", label)
  1236                                                   return self.svc.find(filter_name='tag:Name', filter_value=label)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 1238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1238                                               @dispatch(event="provider.networking.routers.list",
  1239                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1240                                               @profile
  1241                                               def list(self, limit=None, marker=None):
  1242                                                   return self.svc.list(limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 1244

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1244                                               @dispatch(event="provider.networking.routers.create",
  1245                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1246                                               @profile
  1247                                               def create(self, label, network):
  1248                                                   network_id = network.id if isinstance(network, AWSNetwork) else network
  1249                                           
  1250                                                   cb_router = self.svc.create('create_route_table', VpcId=network_id)
  1251                                                   if label:
  1252                                                       cb_router.label = label
  1253                                                   return cb_router

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 1255

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1255                                               @dispatch(event="provider.networking.routers.delete",
  1256                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1257                                               @profile
  1258                                               def delete(self, router):
  1259                                                   r = router if isinstance(router, AWSRouter) else self.get(router)
  1260                                                   if r:
  1261                                                       # pylint:disable=protected-access
  1262                                                       r._route_table.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get_or_create at line 1273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1273                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1274                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1275                                               @profile
  1276                                               def get_or_create(self, network):
  1277                                                   network_id = network.id if isinstance(
  1278                                                       network, AWSNetwork) else network
  1279                                                   # Don't filter by label because it may conflict with at least the
  1280                                                   # default VPC that most accounts have but that network is typically
  1281                                                   # without a name.
  1282                                                   gtw = self.svc.find(filter_name='attachment.vpc-id',
  1283                                                                       filter_value=network_id)
  1284                                                   if gtw:
  1285                                                       return gtw[0]  # There can be only one gtw attached to a VPC
  1286                                                   # Gateway does not exist so create one and attach to the supplied net
  1287                                                   cb_gateway = self.svc.create('create_internet_gateway')
  1288                                                   cb_gateway._gateway.create_tags(
  1289                                                       Tags=[{'Key': 'Name',
  1290                                                              'Value': AWSInternetGateway.CB_DEFAULT_INET_GATEWAY_NAME
  1291                                                              }])
  1292                                                   cb_gateway._gateway.attach_to_vpc(VpcId=network_id)
  1293                                                   return cb_gateway

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 1295

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1295                                               @dispatch(event="provider.networking.gateways.delete",
  1296                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1297                                               @profile
  1298                                               def delete(self, network, gateway):
  1299                                                   gw = (gateway if isinstance(gateway, AWSInternetGateway)
  1300                                                         else self.svc.get(gateway))
  1301                                                   try:
  1302                                                       if gw.network_id:
  1303                                                           # pylint:disable=protected-access
  1304                                                           gw._gateway.detach_from_vpc(VpcId=gw.network_id)
  1305                                                   except ClientError as e:
  1306                                                       log.warn("Error deleting gateway {0}: {1}".format(self.id, e))
  1307                                                   # pylint:disable=protected-access
  1308                                                   gw._gateway.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 1310

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1310                                               @dispatch(event="provider.networking.gateways.list",
  1311                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1312                                               @profile
  1313                                               def list(self, network, limit=None, marker=None):
  1314                                                   log.debug("Listing current AWS internet gateways for net %s.",
  1315                                                             network.id)
  1316                                                   fltr = [{'Name': 'attachment.vpc-id', 'Values': [network.id]}]
  1317                                                   return self.svc.list(limit=None, marker=None, Filters=fltr)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: get at line 1328

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1328                                               @dispatch(event="provider.networking.floating_ips.get",
  1329                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1330                                               @profile
  1331                                               def get(self, gateway, fip_id):
  1332                                                   log.debug("Getting AWS Floating IP Service with the id: %s", fip_id)
  1333                                                   return self.svc.get(fip_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: list at line 1335

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1335                                               @dispatch(event="provider.networking.floating_ips.list",
  1336                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1337                                               @profile
  1338                                               def list(self, gateway, limit=None, marker=None):
  1339                                                   return self.svc.list(limit, marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: create at line 1341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1341                                               @dispatch(event="provider.networking.floating_ips.create",
  1342                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1343                                               @profile
  1344                                               def create(self, gateway):
  1345                                                   log.debug("Creating a floating IP under gateway %s", gateway)
  1346                                                   ip = self.provider.ec2_conn.meta.client.allocate_address(
  1347                                                       Domain='vpc')
  1348                                                   return AWSFloatingIP(
  1349                                                       self.provider,
  1350                                                       self.provider.ec2_conn.VpcAddress(ip.get('AllocationId')))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/aws/services.py
Function: delete at line 1352

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1352                                               @dispatch(event="provider.networking.floating_ips.delete",
  1353                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1354                                               @profile
  1355                                               def delete(self, gateway, fip):
  1356                                                   if isinstance(fip, AWSFloatingIP):
  1357                                                       # pylint:disable=protected-access
  1358                                                       aws_fip = fip._ip
  1359                                                   else:
  1360                                                       aws_fip = self.svc.get_raw(fip)
  1361                                                   aws_fip.release()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 81

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    81                                               @label.setter
    82                                               @profile
    83                                               def label(self, value):
    84                                                   self.assert_valid_resource_label(value)
    85                                                   self._vm_firewall.tags.update(Label=value or "")
    86                                                   self._provider.azure_client.update_vm_firewall_tags(
    87                                                       self.id, self._vm_firewall.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: description at line 93

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    93                                               @description.setter
    94                                               @profile
    95                                               def description(self, value):
    96                                                   self._vm_firewall.tags.update(Description=value or "")
    97                                                   self._provider.azure_client.\
    98                                                       update_vm_firewall_tags(self.id,
    99                                                                               self._vm_firewall.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 105

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   105                                               @profile
   106                                               def refresh(self):
   107                                                   """
   108                                                   Refreshes the security group with tags if required.
   109                                                   """
   110                                                   try:
   111                                                       self._vm_firewall = self._provider.azure_client. \
   112                                                           get_vm_firewall(self.id)
   113                                                       if not self._vm_firewall.tags:
   114                                                           self._vm_firewall.tags = {}
   115                                                   except (CloudError, ValueError) as cloud_error:
   116                                                       log.exception(cloud_error.message)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 265

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   265                                               @profile
   266                                               def refresh(self):
   267                                                   self._key = self._provider.azure_client.get_blob(
   268                                                       self._container.id, self._key.id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 354

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   354                                               @label.setter
   355                                               # pylint:disable=arguments-differ
   356                                               @profile
   357                                               def label(self, value):
   358                                                   """
   359                                                   Set the volume label.
   360                                                   """
   361                                                   self.assert_valid_resource_label(value)
   362                                                   self._volume.tags.update(Label=value or "")
   363                                                   self._provider.azure_client. \
   364                                                       update_disk_tags(self.id,
   365                                                                        self._volume.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: description at line 371

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   371                                               @description.setter
   372                                               @profile
   373                                               def description(self, value):
   374                                                   self._volume.tags.update(Description=value or "")
   375                                                   self._provider.azure_client. \
   376                                                       update_disk_tags(self.id,
   377                                                                        self._volume.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   452                                               @profile
   453                                               def refresh(self):
   454                                                   """
   455                                                   Refreshes the state of this volume by re-querying the cloud provider
   456                                                   for its latest state.
   457                                                   """
   458                                                   try:
   459                                                       self._volume = self._provider.azure_client. \
   460                                                           get_disk(self.id)
   461                                                       self._update_state()
   462                                                   except (CloudError, ValueError) as cloud_error:
   463                                                       log.exception(cloud_error.message)
   464                                                       # The volume no longer exists and cannot be refreshed.
   465                                                       # set the state to unknown
   466                                                       self._state = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 509

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   509                                               @label.setter
   510                                               # pylint:disable=arguments-differ
   511                                               @profile
   512                                               def label(self, value):
   513                                                   """
   514                                                   Set the snapshot label.
   515                                                   """
   516                                                   self.assert_valid_resource_label(value)
   517                                                   self._snapshot.tags.update(Label=value or "")
   518                                                   self._provider.azure_client. \
   519                                                       update_snapshot_tags(self.id,
   520                                                                            self._snapshot.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: description at line 526

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   526                                               @description.setter
   527                                               @profile
   528                                               def description(self, value):
   529                                                   self._snapshot.tags.update(Description=value or "")
   530                                                   self._provider.azure_client. \
   531                                                       update_snapshot_tags(self.id,
   532                                                                            self._snapshot.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 551

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   551                                               @profile
   552                                               def refresh(self):
   553                                                   """
   554                                                   Refreshes the state of this snapshot by re-querying the cloud provider
   555                                                   for its latest state.
   556                                                   """
   557                                                   try:
   558                                                       self._snapshot = self._provider.azure_client. \
   559                                                           get_snapshot(self.id)
   560                                                       self._state = self._snapshot.provisioning_state
   561                                                   except (CloudError, ValueError) as cloud_error:
   562                                                       log.exception(cloud_error.message)
   563                                                       # The snapshot no longer exists and cannot be refreshed.
   564                                                       # set the state to unknown
   565                                                       self._state = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 629

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   629                                               @label.setter
   630                                               @profile
   631                                               def label(self, value):
   632                                                   """
   633                                                   Set the image label when it is a private image.
   634                                                   """
   635                                                   if not self.is_gallery_image:
   636                                                       self.assert_valid_resource_label(value)
   637                                                       self._image.tags.update(Label=value or "")
   638                                                       self._provider.azure_client. \
   639                                                           update_image_tags(self.id, self._image.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: description at line 655

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   655                                               @description.setter
   656                                               @profile
   657                                               def description(self, value):
   658                                                   """
   659                                                   Set the image description.
   660                                                   """
   661                                                   if not self.is_gallery_image:
   662                                                       self._image.tags.update(Description=value or "")
   663                                                       self._provider.azure_client. \
   664                                                           update_image_tags(self.id, self._image.tags)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 705

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   705                                               @profile
   706                                               def refresh(self):
   707                                                   """
   708                                                   Refreshes the state of this instance by re-querying the cloud provider
   709                                                   for its latest state.
   710                                                   """
   711                                                   if not self.is_gallery_image:
   712                                                       try:
   713                                                           self._image = self._provider.azure_client.get_image(self.id)
   714                                                           self._state = self._image.provisioning_state
   715                                                       except CloudError as cloud_error:
   716                                                           log.exception(cloud_error.message)
   717                                                           # image no longer exists
   718                                                           self._state = "unknown"

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
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
   764                                                   self.assert_valid_resource_label(value)
   765                                                   self._network.tags.update(Label=value or "")
   766                                                   self._provider.azure_client. \
   767                                                       update_network_tags(self.id, self._network)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 782

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   782                                               @profile
   783                                               def refresh(self):
   784                                                   """
   785                                                   Refreshes the state of this network by re-querying the cloud provider
   786                                                   for its latest state.
   787                                                   """
   788                                                   try:
   789                                                       self._network = self._provider.azure_client.\
   790                                                           get_network(self.id)
   791                                                       self._state = self._network.provisioning_state
   792                                                   except (CloudError, ValueError) as cloud_error:
   793                                                       log.exception(cloud_error.message)
   794                                                       # The network no longer exists and cannot be refreshed.
   795                                                       # set the state to unknown
   796                                                       self._state = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 852

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   852                                               @profile
   853                                               def refresh(self):
   854                                                   # Gateway is not needed as it doesn't exist in Azure, so just
   855                                                   # getting the Floating IP again from the client
   856                                                   # pylint:disable=protected-access
   857                                                   fip = self._provider.networking._floating_ips.get(None, self.id)
   858                                                   # pylint:disable=protected-access
   859                                                   self._ip = fip._ip

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 957

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   957                                               @label.setter
   958                                               # pylint:disable=arguments-differ
   959                                               @profile
   960                                               def label(self, value):
   961                                                   self.assert_valid_resource_label(value)
   962                                                   network = self.network
   963                                                   # pylint:disable=protected-access
   964                                                   az_network = network._network
   965                                                   kwargs = {self.tag_name: value or ""}
   966                                                   az_network.tags.update(**kwargs)
   967                                                   self._provider.azure_client.update_network_tags(
   968                                                       az_network.id, az_network)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 999

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   999                                               @profile
  1000                                               def refresh(self):
  1001                                                   """
  1002                                                   Refreshes the state of this network by re-querying the cloud provider
  1003                                                   for its latest state.
  1004                                                   """
  1005                                                   try:
  1006                                                       self._subnet = self._provider.azure_client. \
  1007                                                           get_subnet(self.id)
  1008                                                       self._state = self._subnet.provisioning_state
  1009                                                   except (CloudError, ValueError) as cloud_error:
  1010                                                       log.exception(cloud_error.message)
  1011                                                       # The subnet no longer exists and cannot be refreshed.
  1012                                                       # set the state to unknown
  1013                                                       self._state = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: label at line 1086

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1086                                               @label.setter
  1087                                               # pylint:disable=arguments-differ
  1088                                               @profile
  1089                                               def label(self, value):
  1090                                                   """
  1091                                                   Set the instance label.
  1092                                                   """
  1093                                                   self.assert_valid_resource_label(value)
  1094                                                   self._vm.tags.update(Label=value or "")
  1095                                                   self._provider.azure_client. \
  1096                                                       update_vm_tags(self.id, self._vm)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342                                                   """
  1343                                                   Refreshes the state of this instance by re-querying the cloud provider
  1344                                                   for its latest state.
  1345                                                   """
  1346                                                   try:
  1347                                                       self._vm = self._provider.azure_client.get_vm(self.id)
  1348                                                       if not self._vm.tags:
  1349                                                           self._vm.tags = {}
  1350                                                       self._update_state()
  1351                                                   except (CloudError, ValueError) as cloud_error:
  1352                                                       log.exception(cloud_error.message)
  1353                                                       # The volume no longer exists and cannot be refreshed.
  1354                                                       # set the state to unknown
  1355                                                       self._state = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
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
  1468                                                   self.assert_valid_resource_label(value)
  1469                                                   self._route_table.tags.update(Label=value or "")
  1470                                                   self._provider.azure_client. \
  1471                                                       update_route_table_tags(self._route_table.name,
  1472                                                                               self._route_table)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 1474

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1474                                               @profile
  1475                                               def refresh(self):
  1476                                                   self._route_table = self._provider.azure_client. \
  1477                                                       get_route_table(self._route_table.name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py
Function: refresh at line 1533

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1533                                               @profile
  1534                                               def refresh(self):
  1535                                                   pass

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 93

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    93                                               @dispatch(event="provider.security.vm_firewalls.get",
    94                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    95                                               @profile
    96                                               def get(self, vm_firewall_id):
    97                                                   try:
    98                                                       fws = self.provider.azure_client.get_vm_firewall(vm_firewall_id)
    99                                                       return AzureVMFirewall(self.provider, fws)
   100                                                   except (CloudError, InvalidValueException) as cloud_error:
   101                                                       # Azure raises the cloud error if the resource not available
   102                                                       log.exception(cloud_error)
   103                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 105

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   105                                               @dispatch(event="provider.security.vm_firewalls.list",
   106                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   107                                               @profile
   108                                               def list(self, limit=None, marker=None):
   109                                                   fws = [AzureVMFirewall(self.provider, fw)
   110                                                          for fw in self.provider.azure_client.list_vm_firewall()]
   111                                                   return ClientPagedResultList(self.provider, fws, limit, marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 113

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   113                                               @cb_helpers.deprecated_alias(network_id='network')
   114                                               @dispatch(event="provider.security.vm_firewalls.create",
   115                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   116                                               @profile
   117                                               def create(self, label, network, description=None):
   118                                                   AzureVMFirewall.assert_valid_resource_label(label)
   119                                                   name = AzureVMFirewall._generate_name_from_label(label, "cb-fw")
   120                                                   net = network.id if isinstance(network, Network) else network
   121                                                   parameters = {"location": self.provider.region_name,
   122                                                                 "tags": {'Label': label,
   123                                                                          'network_id': net}}
   124                                           
   125                                                   if description:
   126                                                       parameters['tags'].update(Description=description)
   127                                           
   128                                                   fw = self.provider.azure_client.create_vm_firewall(name,
   129                                                                                                      parameters)
   130                                           
   131                                                   # Add default rules to negate azure default rules.
   132                                                   # See: https://github.com/CloudVE/cloudbridge/issues/106
   133                                                   # pylint:disable=protected-access
   134                                                   for rule in fw.default_security_rules:
   135                                                       rule_name = "cb-override-" + rule.name
   136                                                       # Transpose rules to priority 4001 onwards, because
   137                                                       # only 0-4096 are allowed for custom rules
   138                                                       rule.priority = rule.priority - 61440
   139                                                       rule.access = "Deny"
   140                                                       self.provider.azure_client.create_vm_firewall_rule(
   141                                                           fw.id, rule_name, rule)
   142                                           
   143                                                   # Add a new custom rule allowing all outbound traffic to the internet
   144                                                   parameters = {"priority": 3000,
   145                                                                 "protocol": "*",
   146                                                                 "source_port_range": "*",
   147                                                                 "source_address_prefix": "*",
   148                                                                 "destination_port_range": "*",
   149                                                                 "destination_address_prefix": "Internet",
   150                                                                 "access": "Allow",
   151                                                                 "direction": "Outbound"}
   152                                                   result = self.provider.azure_client.create_vm_firewall_rule(
   153                                                       fw.id, "cb-default-internet-outbound", parameters)
   154                                                   fw.security_rules.append(result)
   155                                           
   156                                                   cb_fw = AzureVMFirewall(self.provider, fw)
   157                                                   return cb_fw

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 159

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   159                                               @dispatch(event="provider.security.vm_firewalls.delete",
   160                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   161                                               @profile
   162                                               def delete(self, vm_firewall):
   163                                                   fw_id = (vm_firewall.id if isinstance(vm_firewall, AzureVMFirewall)
   164                                                            else vm_firewall)
   165                                                   self.provider.azure_client.delete_vm_firewall(fw_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
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
   181                                                   rules = [AzureVMFirewallRule(firewall, rule) for rule
   182                                                            in firewall._vm_firewall.security_rules
   183                                                            if rule.priority < 3500]
   184                                                   return ClientPagedResultList(self.provider, rules,
   185                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 187

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   187                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   188                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   189                                               @profile
   190                                               def create(self, firewall, direction, protocol=None, from_port=None,
   191                                                          to_port=None, cidr=None, src_dest_fw=None):
   192                                                   if protocol and from_port and to_port:
   193                                                       return self._create_rule(firewall, direction, protocol, from_port,
   194                                                                                to_port, cidr)
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

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   238                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   239                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   240                                               @profile
   241                                               def delete(self, firewall, rule):
   242                                                   rule_id = rule.id if isinstance(rule, AzureVMFirewallRule) else rule
   243                                                   fw_name = firewall.name
   244                                                   self.provider.azure_client. \
   245                                                       delete_vm_firewall_rule(rule_id, fw_name)
   246                                                   for i, o in enumerate(firewall._vm_firewall.security_rules):
   247                                                       if o.id == rule_id:
   248                                                           # pylint:disable=protected-access
   249                                                           del firewall._vm_firewall.security_rules[i]
   250                                                           break

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 259

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   259                                               @dispatch(event="provider.security.key_pairs.get",
   260                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   261                                               @profile
   262                                               def get(self, key_pair_id):
   263                                                   try:
   264                                                       key_pair = self.provider.azure_client.\
   265                                                           get_public_key(key_pair_id)
   266                                           
   267                                                       if key_pair:
   268                                                           return AzureKeyPair(self.provider, key_pair)
   269                                                       return None
   270                                                   except AzureException as error:
   271                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   272                                                       log.debug(error)
   273                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 275

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   275                                               @dispatch(event="provider.security.key_pairs.list",
   276                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   277                                               @profile
   278                                               def list(self, limit=None, marker=None):
   279                                                   key_pairs, resume_marker = self.provider.azure_client.list_public_keys(
   280                                                       AzureKeyPairService.PARTITION_KEY, marker=marker,
   281                                                       limit=limit or self.provider.config.default_result_limit)
   282                                                   results = [AzureKeyPair(self.provider, key_pair)
   283                                                              for key_pair in key_pairs]
   284                                                   return ServerPagedResultList(is_truncated=resume_marker,
   285                                                                                marker=resume_marker,
   286                                                                                supports_total=False,
   287                                                                                data=results)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 289

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   289                                               @dispatch(event="provider.security.key_pairs.find",
   290                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   291                                               @profile
   292                                               def find(self, **kwargs):
   293                                                   obj_list = self
   294                                                   filters = ['name']
   295                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   296                                           
   297                                                   # All kwargs should have been popped at this time.
   298                                                   if len(kwargs) > 0:
   299                                                       raise InvalidParamException(
   300                                                           "Unrecognised parameters for search: %s. Supported "
   301                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   302                                           
   303                                                   return ClientPagedResultList(self.provider,
   304                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.key_pairs.create",
   307                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, name, public_key_material=None):
   310                                                   AzureKeyPair.assert_valid_resource_name(name)
   311                                                   key_pair = self.get(name)
   312                                           
   313                                                   if key_pair:
   314                                                       raise DuplicateResourceException(
   315                                                           'Keypair already exists with name {0}'.format(name))
   316                                           
   317                                                   private_key = None
   318                                                   if not public_key_material:
   319                                                       public_key_material, private_key = cb_helpers.generate_key_pair()
   320                                           
   321                                                   entity = {
   322                                                       'PartitionKey': AzureKeyPairService.PARTITION_KEY,
   323                                                       'RowKey': str(uuid.uuid4()),
   324                                                       'Name': name,
   325                                                       'Key': public_key_material
   326                                                   }
   327                                           
   328                                                   self.provider.azure_client.create_public_key(entity)
   329                                                   key_pair = self.get(name)
   330                                                   key_pair.material = private_key
   331                                                   return key_pair

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 333

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   333                                               @dispatch(event="provider.security.key_pairs.delete",
   334                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   335                                               @profile
   336                                               def delete(self, key_pair):
   337                                                   key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
   338                                                               self.get(key_pair))
   339                                                   if key_pair:
   340                                                       # pylint:disable=protected-access
   341                                                       self.provider.azure_client.delete_public_key(key_pair._key_pair)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.storage.volumes.get",
   376                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def get(self, volume_id):
   379                                                   try:
   380                                                       volume = self.provider.azure_client.get_disk(volume_id)
   381                                                       return AzureVolume(self.provider, volume)
   382                                                   except (CloudError, InvalidValueException) as cloud_error:
   383                                                       # Azure raises the cloud error if the resource not available
   384                                                       log.exception(cloud_error)
   385                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 387

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   387                                               @dispatch(event="provider.storage.volumes.find",
   388                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   389                                               @profile
   390                                               def find(self, **kwargs):
   391                                                   obj_list = self
   392                                                   filters = ['label']
   393                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   394                                           
   395                                                   # All kwargs should have been popped at this time.
   396                                                   if len(kwargs) > 0:
   397                                                       raise InvalidParamException(
   398                                                           "Unrecognised parameters for search: %s. Supported "
   399                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   400                                           
   401                                                   return ClientPagedResultList(self.provider,
   402                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 404

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   404                                               @dispatch(event="provider.storage.volumes.list",
   405                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   406                                               @profile
   407                                               def list(self, limit=None, marker=None):
   408                                                   azure_vols = self.provider.azure_client.list_disks()
   409                                                   cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
   410                                                   return ClientPagedResultList(self.provider, cb_vols,
   411                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 413

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   413                                               @dispatch(event="provider.storage.volumes.create",
   414                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   415                                               @profile
   416                                               def create(self, label, size, zone, snapshot=None, description=None):
   417                                                   AzureVolume.assert_valid_resource_label(label)
   418                                                   disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
   419                                                   tags = {'Label': label}
   420                                           
   421                                                   zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   422                                                   snapshot = (self.provider.storage.snapshots.get(snapshot)
   423                                                               if snapshot and isinstance(snapshot, str) else snapshot)
   424                                           
   425                                                   if description:
   426                                                       tags.update(Description=description)
   427                                           
   428                                                   if snapshot:
   429                                                       params = {
   430                                                           'location':
   431                                                               zone_id or self.provider.azure_client.region_name,
   432                                                           'creation_data': {
   433                                                               'create_option': DiskCreateOption.copy,
   434                                                               'source_uri': snapshot.resource_id
   435                                                           },
   436                                                           'tags': tags
   437                                                       }
   438                                           
   439                                                       disk = self.provider.azure_client.create_snapshot_disk(disk_name,
   440                                                                                                              params)
   441                                           
   442                                                   else:
   443                                                       params = {
   444                                                           'location':
   445                                                               zone_id or self.provider.region_name,
   446                                                           'disk_size_gb': size,
   447                                                           'creation_data': {
   448                                                               'create_option': DiskCreateOption.empty
   449                                                           },
   450                                                           'tags': tags
   451                                                       }
   452                                           
   453                                                       disk = self.provider.azure_client.create_empty_disk(disk_name,
   454                                                                                                           params)
   455                                           
   456                                                   azure_vol = self.provider.azure_client.get_disk(disk.id)
   457                                                   cb_vol = AzureVolume(self.provider, azure_vol)
   458                                           
   459                                                   return cb_vol

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 461

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   461                                               @dispatch(event="provider.storage.volumes.delete",
   462                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   463                                               @profile
   464                                               def delete(self, volume_id):
   465                                                   vol_id = (volume_id.id if isinstance(volume_id, AzureVolume)
   466                                                             else volume_id)
   467                                                   self.provider.azure_client.delete_disk(vol_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 474

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   474                                               @dispatch(event="provider.storage.snapshots.get",
   475                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   476                                               @profile
   477                                               def get(self, snapshot_id):
   478                                                   try:
   479                                                       snapshot = self.provider.azure_client.get_snapshot(snapshot_id)
   480                                                       return AzureSnapshot(self.provider, snapshot)
   481                                                   except (CloudError, InvalidValueException) as cloud_error:
   482                                                       # Azure raises the cloud error if the resource not available
   483                                                       log.exception(cloud_error)
   484                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 486

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   486                                               @dispatch(event="provider.storage.snapshots.find",
   487                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   488                                               @profile
   489                                               def find(self, **kwargs):
   490                                                   obj_list = self
   491                                                   filters = ['label']
   492                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   493                                           
   494                                                   # All kwargs should have been popped at this time.
   495                                                   if len(kwargs) > 0:
   496                                                       raise InvalidParamException(
   497                                                           "Unrecognised parameters for search: %s. Supported "
   498                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   499                                           
   500                                                   return ClientPagedResultList(self.provider,
   501                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 503

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   503                                               @dispatch(event="provider.storage.snapshots.list",
   504                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   505                                               @profile
   506                                               def list(self, limit=None, marker=None):
   507                                                   snaps = [AzureSnapshot(self.provider, obj)
   508                                                            for obj in
   509                                                            self.provider.azure_client.list_snapshots()]
   510                                                   return ClientPagedResultList(self.provider, snaps, limit, marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 512

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   512                                               @dispatch(event="provider.storage.snapshots.create",
   513                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   514                                               @profile
   515                                               def create(self, label, volume, description=None):
   516                                                   AzureSnapshot.assert_valid_resource_label(label)
   517                                                   snapshot_name = AzureSnapshot._generate_name_from_label(label,
   518                                                                                                           "cb-snap")
   519                                                   tags = {'Label': label}
   520                                                   if description:
   521                                                       tags.update(Description=description)
   522                                           
   523                                                   volume = (self.provider.storage.volumes.get(volume)
   524                                                             if isinstance(volume, str) else volume)
   525                                           
   526                                                   params = {
   527                                                       'location': self.provider.azure_client.region_name,
   528                                                       'creation_data': {
   529                                                           'create_option': DiskCreateOption.copy,
   530                                                           'source_uri': volume.resource_id
   531                                                       },
   532                                                       'disk_size_gb': volume.size,
   533                                                       'tags': tags
   534                                                   }
   535                                           
   536                                                   azure_snap = self.provider.azure_client.create_snapshot(snapshot_name,
   537                                                                                                           params)
   538                                                   return AzureSnapshot(self.provider, azure_snap)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 540

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   540                                               @dispatch(event="provider.storage.snapshots.delete",
   541                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   542                                               @profile
   543                                               def delete(self, snapshot_id):
   544                                                   snap_id = (snapshot_id.id if isinstance(snapshot_id, AzureSnapshot)
   545                                                              else snapshot_id)
   546                                                   self.provider.azure_client.delete_snapshot(snap_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 553

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   553                                               @dispatch(event="provider.storage.buckets.get",
   554                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   555                                               @profile
   556                                               def get(self, bucket_id):
   557                                                   """
   558                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   559                                                   does not exist.
   560                                                   """
   561                                                   try:
   562                                                       bucket = self.provider.azure_client.get_container(bucket_id)
   563                                                       return AzureBucket(self.provider, bucket)
   564                                                   except AzureException as error:
   565                                                       log.exception(error)
   566                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 568

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   568                                               @dispatch(event="provider.storage.buckets.list",
   569                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   570                                               @profile
   571                                               def list(self, limit=None, marker=None):
   572                                                   buckets = [AzureBucket(self.provider, bucket)
   573                                                              for bucket
   574                                                              in self.provider.azure_client.list_containers()[0]]
   575                                                   return ClientPagedResultList(self.provider, buckets,
   576                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 578

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   578                                               @dispatch(event="provider.storage.buckets.create",
   579                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   580                                               @profile
   581                                               def create(self, name, location=None):
   582                                                   """
   583                                                   Create a new bucket.
   584                                                   """
   585                                                   AzureBucket.assert_valid_resource_name(name)
   586                                                   bucket = self.provider.azure_client.create_container(name)
   587                                                   return AzureBucket(self.provider, bucket)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 589

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   589                                               @dispatch(event="provider.storage.buckets.delete",
   590                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   591                                               @profile
   592                                               def delete(self, bucket):
   593                                                   """
   594                                                   Delete this bucket.
   595                                                   """
   596                                                   b_id = bucket.id if isinstance(bucket, AzureBucket) else bucket
   597                                                   self.provider.azure_client.delete_container(b_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 604

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   604                                               @profile
   605                                               def get(self, bucket, object_id):
   606                                                   """
   607                                                   Retrieve a given object from this bucket.
   608                                                   """
   609                                                   try:
   610                                                       obj = self.provider.azure_client.get_blob(bucket.name,
   611                                                                                                 object_id)
   612                                                       return AzureBucketObject(self.provider, bucket, obj)
   613                                                   except AzureException as azureEx:
   614                                                       log.exception(azureEx)
   615                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 617

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   617                                               @profile
   618                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   619                                                   """
   620                                                   List all objects within this bucket.
   621                                           
   622                                                   :rtype: BucketObject
   623                                                   :return: List of all available BucketObjects within this bucket.
   624                                                   """
   625                                                   objects = [AzureBucketObject(self.provider, bucket, obj)
   626                                                              for obj in
   627                                                              self.provider.azure_client.list_blobs(
   628                                                                  bucket.name, prefix=prefix)]
   629                                                   return ClientPagedResultList(self.provider, objects,
   630                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 632

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   632                                               @profile
   633                                               def find(self, bucket, **kwargs):
   634                                                   obj_list = [AzureBucketObject(self.provider, bucket, obj)
   635                                                               for obj in
   636                                                               self.provider.azure_client.list_blobs(bucket.name)]
   637                                                   filters = ['name']
   638                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   639                                                   return ClientPagedResultList(self.provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 641

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   641                                               @profile
   642                                               def create(self, bucket, name):
   643                                                   self.provider.azure_client.create_blob_from_text(
   644                                                       bucket.name, name, '')
   645                                                   return self.get(bucket, name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @profile
   678                                               def get(self, image_id):
   679                                                   """
   680                                                   Returns an Image given its id
   681                                                   """
   682                                                   try:
   683                                                       image = self.provider.azure_client.get_image(image_id)
   684                                                       return AzureMachineImage(self.provider, image)
   685                                                   except (CloudError, InvalidValueException) as cloud_error:
   686                                                       # Azure raises the cloud error if the resource not available
   687                                                       log.exception(cloud_error)
   688                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 690

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   690                                               @profile
   691                                               def find(self, **kwargs):
   692                                                   obj_list = self
   693                                                   filters = ['label']
   694                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   695                                           
   696                                                   # All kwargs should have been popped at this time.
   697                                                   if len(kwargs) > 0:
   698                                                       raise InvalidParamException(
   699                                                           "Unrecognised parameters for search: %s. Supported "
   700                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   701                                           
   702                                                   return ClientPagedResultList(self.provider,
   703                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 705

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   705                                               @profile
   706                                               def list(self, filter_by_owner=True, limit=None, marker=None):
   707                                                   """
   708                                                   List all images.
   709                                                   """
   710                                                   azure_images = self.provider.azure_client.list_images()
   711                                                   azure_gallery_refs = self.provider.azure_client.list_gallery_refs() \
   712                                                       if not filter_by_owner else []
   713                                                   cb_images = [AzureMachineImage(self.provider, img)
   714                                                                for img in azure_images + azure_gallery_refs]
   715                                                   return ClientPagedResultList(self.provider, cb_images,
   716                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create_launch_config at line 859

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   859                                               @profile
   860                                               def create_launch_config(self):
   861                                                   return AzureLaunchConfig(self.provider)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 863

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   863                                               @dispatch(event="provider.compute.instances.create",
   864                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   865                                               @profile
   866                                               def create(self, label, image, vm_type, subnet, zone,
   867                                                          key_pair=None, vm_firewalls=None, user_data=None,
   868                                                          launch_config=None, **kwargs):
   869                                                   AzureInstance.assert_valid_resource_label(label)
   870                                                   instance_name = AzureInstance._generate_name_from_label(label,
   871                                                                                                           "cb-ins")
   872                                           
   873                                                   image = (image if isinstance(image, AzureMachineImage) else
   874                                                            self.provider.compute.images.get(image))
   875                                                   if not isinstance(image, AzureMachineImage):
   876                                                       raise Exception("Provided image %s is not a valid azure image"
   877                                                                       % image)
   878                                           
   879                                                   instance_size = vm_type.id if \
   880                                                       isinstance(vm_type, VMType) else vm_type
   881                                           
   882                                                   if not subnet:
   883                                                       # Azure has only a single zone per region; use the current one
   884                                                       zone = self.provider.compute.regions.get(
   885                                                           self.provider.region_name).zones[0]
   886                                                       subnet = self.provider.networking.subnets.get_or_create_default(
   887                                                           zone)
   888                                                   else:
   889                                                       subnet = (self.provider.networking.subnets.get(subnet)
   890                                                                 if isinstance(subnet, str) else subnet)
   891                                           
   892                                                   zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   893                                           
   894                                                   subnet_id, zone_id, vm_firewall_id = \
   895                                                       self._resolve_launch_options(instance_name,
   896                                                                                    subnet, zone_id, vm_firewalls)
   897                                           
   898                                                   storage_profile = self._create_storage_profile(image, launch_config,
   899                                                                                                  instance_name, zone_id)
   900                                           
   901                                                   nic_params = {
   902                                                       'location': self.provider.region_name,
   903                                                       'ip_configurations': [{
   904                                                           'name': instance_name + '_ip_config',
   905                                                           'private_ip_allocation_method': 'Dynamic',
   906                                                           'subnet': {
   907                                                               'id': subnet_id
   908                                                           }
   909                                                       }]
   910                                                   }
   911                                           
   912                                                   if vm_firewall_id:
   913                                                       nic_params['network_security_group'] = {
   914                                                           'id': vm_firewall_id
   915                                                       }
   916                                                   nic_info = self.provider.azure_client.create_nic(
   917                                                       instance_name + '_nic',
   918                                                       nic_params
   919                                                   )
   920                                                   # #! indicates shell script
   921                                                   ud = '#cloud-config\n' + user_data \
   922                                                       if user_data and not user_data.startswith('#!')\
   923                                                       and not user_data.startswith('#cloud-config') else user_data
   924                                           
   925                                                   # Key_pair is mandatory in azure and it should not be None.
   926                                                   temp_key_pair = None
   927                                                   if key_pair:
   928                                                       key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
   929                                                                   else self.provider.security.key_pairs.get(key_pair))
   930                                                   else:
   931                                                       # Create a temporary keypair if none is provided to keep Azure
   932                                                       # happy, but the private key will be discarded, so it'll be all
   933                                                       # but useless. However, this will allow an instance to be launched
   934                                                       # without specifying a keypair, so users may still be able to login
   935                                                       # if they have a preinstalled keypair/password baked into the image
   936                                                       temp_kp_name = "".join(["cb-default-kp-",
   937                                                                              str(uuid.uuid5(uuid.NAMESPACE_OID,
   938                                                                                             instance_name))[-6:]])
   939                                                       key_pair = self.provider.security.key_pairs.create(
   940                                                           name=temp_kp_name)
   941                                                       temp_key_pair = key_pair
   942                                           
   943                                                   params = {
   944                                                       'location': zone_id or self.provider.region_name,
   945                                                       'os_profile': {
   946                                                           'admin_username': self.provider.vm_default_user_name,
   947                                                           'computer_name': instance_name,
   948                                                           'linux_configuration': {
   949                                                               "disable_password_authentication": True,
   950                                                               "ssh": {
   951                                                                   "public_keys": [{
   952                                                                       "path":
   953                                                                           "/home/{}/.ssh/authorized_keys".format(
   954                                                                                   self.provider.vm_default_user_name),
   955                                                                           "key_data": key_pair._key_pair.Key
   956                                                                   }]
   957                                                               }
   958                                                           }
   959                                                       },
   960                                                       'hardware_profile': {
   961                                                           'vm_size': instance_size
   962                                                       },
   963                                                       'network_profile': {
   964                                                           'network_interfaces': [{
   965                                                               'id': nic_info.id
   966                                                           }]
   967                                                       },
   968                                                       'storage_profile': storage_profile,
   969                                                       'tags': {'Label': label}
   970                                                   }
   971                                           
   972                                                   for disk_def in storage_profile.get('data_disks', []):
   973                                                       params['tags'] = dict(disk_def.get('tags', {}), **params['tags'])
   974                                           
   975                                                   if user_data:
   976                                                       custom_data = base64.b64encode(bytes(ud, 'utf-8'))
   977                                                       params['os_profile']['custom_data'] = str(custom_data, 'utf-8')
   978                                           
   979                                                   if not temp_key_pair:
   980                                                       params['tags'].update(Key_Pair=key_pair.id)
   981                                           
   982                                                   try:
   983                                                       vm = self.provider.azure_client.create_vm(instance_name, params)
   984                                                   except Exception as e:
   985                                                       # If VM creation fails, attempt to clean up intermediary resources
   986                                                       self.provider.azure_client.delete_nic(nic_info.id)
   987                                                       for disk_def in storage_profile.get('data_disks', []):
   988                                                           if disk_def.get('tags', {}).get('delete_on_terminate'):
   989                                                               disk_id = disk_def.get('managed_disk', {}).get('id')
   990                                                               if disk_id:
   991                                                                   vol = self.provider.storage.volumes.get(disk_id)
   992                                                                   vol.delete()
   993                                                       raise e
   994                                                   finally:
   995                                                       if temp_key_pair:
   996                                                           temp_key_pair.delete()
   997                                                   return AzureInstance(self.provider, vm)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 999

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   999                                               @dispatch(event="provider.compute.instances.list",
  1000                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
  1001                                               @profile
  1002                                               def list(self, limit=None, marker=None):
  1003                                                   """
  1004                                                   List all instances.
  1005                                                   """
  1006                                                   instances = [AzureInstance(self.provider, inst)
  1007                                                                for inst in self.provider.azure_client.list_vm()]
  1008                                                   return ClientPagedResultList(self.provider, instances,
  1009                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 1011

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1011                                               @dispatch(event="provider.compute.instances.get",
  1012                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
  1013                                               @profile
  1014                                               def get(self, instance_id):
  1015                                                   """
  1016                                                   Returns an instance given its id. Returns None
  1017                                                   if the object does not exist.
  1018                                                   """
  1019                                                   try:
  1020                                                       vm = self.provider.azure_client.get_vm(instance_id)
  1021                                                       return AzureInstance(self.provider, vm)
  1022                                                   except (CloudError, InvalidValueException) as cloud_error:
  1023                                                       # Azure raises the cloud error if the resource not available
  1024                                                       log.exception(cloud_error)
  1025                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 1027

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1027                                               @dispatch(event="provider.compute.instances.find",
  1028                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
  1029                                               @profile
  1030                                               def find(self, **kwargs):
  1031                                                   obj_list = self
  1032                                                   filters = ['label']
  1033                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1034                                           
  1035                                                   # All kwargs should have been popped at this time.
  1036                                                   if len(kwargs) > 0:
  1037                                                       raise InvalidParamException(
  1038                                                           "Unrecognised parameters for search: %s. Supported "
  1039                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
  1040                                           
  1041                                                   return ClientPagedResultList(self.provider,
  1042                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1044

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1044                                               @dispatch(event="provider.compute.instances.delete",
  1045                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
  1046                                               @profile
  1047                                               def delete(self, instance):
  1048                                                   """
  1049                                                   Permanently terminate this instance.
  1050                                                   After deleting the VM. we are deleting the network interface
  1051                                                   associated to the instance, and also removing OS disk and data disks
  1052                                                   where tag with name 'delete_on_terminate' has value True.
  1053                                                   """
  1054                                                   ins = (instance if isinstance(instance, AzureInstance) else
  1055                                                          self.get(instance))
  1056                                                   if not instance:
  1057                                                       return
  1058                                           
  1059                                                   # Remove IPs first to avoid a network interface conflict
  1060                                                   # pylint:disable=protected-access
  1061                                                   for public_ip_id in ins._public_ip_ids:
  1062                                                       ins.remove_floating_ip(public_ip_id)
  1063                                                   self.provider.azure_client.deallocate_vm(ins.id)
  1064                                                   self.provider.azure_client.delete_vm(ins.id)
  1065                                                   # pylint:disable=protected-access
  1066                                                   for nic_id in ins._nic_ids:
  1067                                                       self.provider.azure_client.delete_nic(nic_id)
  1068                                                   # pylint:disable=protected-access
  1069                                                   for data_disk in ins._vm.storage_profile.data_disks:
  1070                                                       if data_disk.managed_disk:
  1071                                                           # pylint:disable=protected-access
  1072                                                           if ins._vm.tags.get('delete_on_terminate',
  1073                                                                               'False') == 'True':
  1074                                                               self.provider.azure_client. \
  1075                                                                   delete_disk(data_disk.managed_disk.id)
  1076                                                   # pylint:disable=protected-access
  1077                                                   if ins._vm.storage_profile.os_disk.managed_disk:
  1078                                                       self.provider.azure_client. \
  1079                                                           delete_disk(ins._vm.storage_profile.os_disk.managed_disk.id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1095

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1095                                               @dispatch(event="provider.compute.vm_types.list",
  1096                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
  1097                                               @profile
  1098                                               def list(self, limit=None, marker=None):
  1099                                                   vm_types = [AzureVMType(self.provider, vm_type)
  1100                                                               for vm_type in self.instance_data]
  1101                                                   return ClientPagedResultList(self.provider, vm_types,
  1102                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113                                                   region = None
  1114                                                   for azureRegion in self.provider.azure_client.list_locations():
  1115                                                       if azureRegion.name == region_id:
  1116                                                           region = AzureRegion(self.provider, azureRegion)
  1117                                                           break
  1118                                                   return region

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1120

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1120                                               @dispatch(event="provider.compute.regions.list",
  1121                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1122                                               @profile
  1123                                               def list(self, limit=None, marker=None):
  1124                                                   regions = [AzureRegion(self.provider, region)
  1125                                                              for region in self.provider.azure_client.list_locations()]
  1126                                                   return ClientPagedResultList(self.provider, regions,
  1127                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172                                                   try:
  1173                                                       network = self.provider.azure_client.get_network(network_id)
  1174                                                       return AzureNetwork(self.provider, network)
  1175                                                   except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177                                                       log.exception(cloud_error)
  1178                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184                                                   networks = [AzureNetwork(self.provider, network)
  1185                                                               for network in self.provider.azure_client.list_networks()]
  1186                                                   return ClientPagedResultList(self.provider, networks,
  1187                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 1189

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1189                                               @dispatch(event="provider.networking.networks.create",
  1190                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1191                                               @profile
  1192                                               def create(self, label, cidr_block):
  1193                                                   AzureNetwork.assert_valid_resource_label(label)
  1194                                                   params = {
  1195                                                       'location': self.provider.azure_client.region_name,
  1196                                                       'address_space': {
  1197                                                           'address_prefixes': [cidr_block]
  1198                                                       },
  1199                                                       'tags': {'Label': label}
  1200                                                   }
  1201                                           
  1202                                                   network_name = AzureNetwork._generate_name_from_label(label, 'cb-net')
  1203                                           
  1204                                                   az_network = self.provider.azure_client.create_network(network_name,
  1205                                                                                                          params)
  1206                                                   cb_network = AzureNetwork(self.provider, az_network)
  1207                                                   return cb_network

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1209

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1209                                               @dispatch(event="provider.networking.networks.delete",
  1210                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1211                                               @profile
  1212                                               def delete(self, network):
  1213                                                   net_id = network.id if isinstance(network, AzureNetwork) else network
  1214                                                   if net_id:
  1215                                                       self.provider.azure_client.delete_network(net_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
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
  1255                                                   try:
  1256                                                       azure_subnet = self.provider.azure_client.get_subnet(subnet_id)
  1257                                                       return AzureSubnet(self.provider,
  1258                                                                          azure_subnet) if azure_subnet else None
  1259                                                   except (CloudError, InvalidValueException) as cloud_error:
  1260                                                       # Azure raises the cloud error if the resource not available
  1261                                                       log.exception(cloud_error)
  1262                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1264

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1264                                               @dispatch(event="provider.networking.subnets.list",
  1265                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1266                                               @profile
  1267                                               def list(self, network=None, limit=None, marker=None):
  1268                                                   return ClientPagedResultList(self.provider,
  1269                                                                                self._list_subnets(network),
  1270                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276                                                   obj_list = self._list_subnets(network)
  1277                                                   filters = ['label']
  1278                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280                                                   return ClientPagedResultList(self.provider,
  1281                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 1283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1283                                               @dispatch(event="provider.networking.subnets.create",
  1284                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1285                                               @profile
  1286                                               def create(self, label, network, cidr_block, zone):
  1287                                                   AzureSubnet.assert_valid_resource_label(label)
  1288                                                   # Although Subnet doesn't support tags in Azure, we use the parent
  1289                                                   # Network's tags to track its subnets' labels
  1290                                                   subnet_name = AzureSubnet._generate_name_from_label(label, "cb-sn")
  1291                                           
  1292                                                   network_id = network.id \
  1293                                                       if isinstance(network, Network) else network
  1294                                           
  1295                                                   subnet_info = self.provider.azure_client\
  1296                                                       .create_subnet(
  1297                                                           network_id,
  1298                                                           subnet_name,
  1299                                                           {
  1300                                                               'address_prefix': cidr_block
  1301                                                           }
  1302                                                       )
  1303                                           
  1304                                                   subnet = AzureSubnet(self.provider, subnet_info)
  1305                                                   subnet.label = label
  1306                                                   return subnet

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1308                                               @dispatch(event="provider.networking.subnets.delete",
  1309                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1310                                               @profile
  1311                                               def delete(self, subnet):
  1312                                                   sn = subnet if isinstance(subnet, AzureSubnet) else self.get(subnet)
  1313                                                   if sn:
  1314                                                       self.provider.azure_client.delete_subnet(sn.id)
  1315                                                       # Although Subnet doesn't support labels, we use the parent
  1316                                                       # Network's tags to track the subnet's labels, thus that
  1317                                                       # network-level tag must be deleted with the subnet
  1318                                                       net_id = sn.network_id
  1319                                                       az_network = self.provider.azure_client.get_network(net_id)
  1320                                                       az_network.tags.pop(sn.tag_name)
  1321                                                       self.provider.azure_client.update_network_tags(
  1322                                                           az_network.id, az_network)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 1329

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1329                                               @dispatch(event="provider.networking.routers.get",
  1330                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1331                                               @profile
  1332                                               def get(self, router_id):
  1333                                                   try:
  1334                                                       route = self.provider.azure_client.get_route_table(router_id)
  1335                                                       return AzureRouter(self.provider, route)
  1336                                                   except (CloudError, InvalidValueException) as cloud_error:
  1337                                                       # Azure raises the cloud error if the resource not available
  1338                                                       log.exception(cloud_error)
  1339                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: find at line 1341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1341                                               @dispatch(event="provider.networking.routers.find",
  1342                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1343                                               @profile
  1344                                               def find(self, **kwargs):
  1345                                                   obj_list = self
  1346                                                   filters = ['label']
  1347                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1348                                           
  1349                                                   # All kwargs should have been popped at this time.
  1350                                                   if len(kwargs) > 0:
  1351                                                       raise InvalidParamException(
  1352                                                           "Unrecognised parameters for search: %s. Supported "
  1353                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
  1354                                           
  1355                                                   return ClientPagedResultList(self.provider,
  1356                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1358

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1358                                               @dispatch(event="provider.networking.routers.list",
  1359                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1360                                               @profile
  1361                                               def list(self, limit=None, marker=None):
  1362                                                   routes = [AzureRouter(self.provider, route)
  1363                                                             for route in
  1364                                                             self.provider.azure_client.list_route_tables()]
  1365                                                   return ClientPagedResultList(self.provider,
  1366                                                                                routes,
  1367                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 1369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1369                                               @dispatch(event="provider.networking.routers.create",
  1370                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1371                                               @profile
  1372                                               def create(self, label, network):
  1373                                                   router_name = AzureRouter._generate_name_from_label(label, "cb-router")
  1374                                           
  1375                                                   parameters = {"location": self.provider.region_name,
  1376                                                                 "tags": {'Label': label}}
  1377                                           
  1378                                                   route = self.provider.azure_client. \
  1379                                                       create_route_table(router_name, parameters)
  1380                                                   return AzureRouter(self.provider, route)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1382                                               @dispatch(event="provider.networking.routers.delete",
  1383                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1384                                               @profile
  1385                                               def delete(self, router):
  1386                                                   r = router if isinstance(router, AzureRouter) else self.get(router)
  1387                                                   if r:
  1388                                                       self.provider.azure_client.delete_route_table(r.name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get_or_create at line 1403

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1403                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1404                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1405                                               @profile
  1406                                               def get_or_create(self, network):
  1407                                                   return self._gateway_singleton(network)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1409

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1409                                               @dispatch(event="provider.networking.gateways.list",
  1410                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1411                                               @profile
  1412                                               def list(self, network, limit=None, marker=None):
  1413                                                   gws = [self._gateway_singleton(network)]
  1414                                                   return ClientPagedResultList(self.provider,
  1415                                                                                gws,
  1416                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1418

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1418                                               @dispatch(event="provider.networking.gateways.delete",
  1419                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1420                                               @profile
  1421                                               def delete(self, network, gateway):
  1422                                                   pass

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: get at line 1430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1430                                               @dispatch(event="provider.networking.floating_ips.get",
  1431                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1432                                               @profile
  1433                                               def get(self, gateway, fip_id):
  1434                                                   try:
  1435                                                       az_ip = self.provider.azure_client.get_floating_ip(fip_id)
  1436                                                   except (CloudError, InvalidValueException) as cloud_error:
  1437                                                       # Azure raises the cloud error if the resource not available
  1438                                                       log.exception(cloud_error)
  1439                                                       return None
  1440                                                   return AzureFloatingIP(self.provider, az_ip)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: list at line 1442

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1442                                               @dispatch(event="provider.networking.floating_ips.list",
  1443                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1444                                               @profile
  1445                                               def list(self, gateway, limit=None, marker=None):
  1446                                                   floating_ips = [AzureFloatingIP(self.provider, floating_ip)
  1447                                                                   for floating_ip in self.provider.azure_client.
  1448                                                                   list_floating_ips()]
  1449                                                   return ClientPagedResultList(self.provider, floating_ips,
  1450                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: create at line 1452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1452                                               @dispatch(event="provider.networking.floating_ips.create",
  1453                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1454                                               @profile
  1455                                               def create(self, gateway):
  1456                                                   public_ip_parameters = {
  1457                                                       'location': self.provider.azure_client.region_name,
  1458                                                       'public_ip_allocation_method': 'Static'
  1459                                                   }
  1460                                           
  1461                                                   public_ip_name = AzureFloatingIP._generate_name_from_label(
  1462                                                       None, 'cb-fip-')
  1463                                           
  1464                                                   floating_ip = self.provider.azure_client.\
  1465                                                       create_floating_ip(public_ip_name, public_ip_parameters)
  1466                                                   return AzureFloatingIP(self.provider, floating_ip)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py
Function: delete at line 1468

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1468                                               @dispatch(event="provider.networking.floating_ips.delete",
  1469                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1470                                               @profile
  1471                                               def delete(self, gateway, fip):
  1472                                                   fip_id = fip.id if isinstance(fip, AzureFloatingIP) else fip
  1473                                                   self.provider.azure_client.delete_floating_ip(fip_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 482

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   482                                               @label.setter
   483                                               @profile
   484                                               def label(self, value):
   485                                                   self.assert_valid_resource_label(value)
   486                                                   tag_name = "_".join(["firewall", self.name, "label"])
   487                                                   helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: description at line 508

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   508                                               @description.setter
   509                                               @profile
   510                                               def description(self, value):
   511                                                   # Change the description on all rules
   512                                                   for fw in self._delegate.iter_firewalls(self._vm_firewall,
   513                                                                                           self._network.name):
   514                                                       fw['description'] = value or ''
   515                                                       response = (self._provider
   516                                                                   .gcp_compute
   517                                                                   .firewalls()
   518                                                                   .update(project=self._provider.project_name,
   519                                                                           firewall=fw['name'],
   520                                                                           body=fw)
   521                                                                   .execute())
   522                                                       self._provider.wait_for_operation(response)
   523                                                   # Set back to None so that the next time the user gets it, it updates
   524                                                   # but don't force update here to avoid more overhead
   525                                                   self._description = None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 542

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   542                                               @profile
   543                                               def refresh(self):
   544                                                   fw = self._provider.security.vm_firewalls.get(self.id)
   545                                                   # restore all internal state
   546                                                   if fw:
   547                                                       # pylint:disable=protected-access
   548                                                       self._delegate = fw._delegate
   549                                                       # pylint:disable=protected-access
   550                                                       self._description = fw._description
   551                                                       # pylint:disable=protected-access
   552                                                       self._network = fw._network
   553                                                       # pylint:disable=protected-access
   554                                                       self._rule_container = fw._rule_container

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 713

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   713                                               @label.setter
   714                                               # pylint:disable=arguments-differ
   715                                               @profile
   716                                               def label(self, value):
   717                                                   req = (self._provider
   718                                                              .gcp_compute
   719                                                              .images()
   720                                                              .setLabels(project=self._provider.project_name,
   721                                                                         resource=self.name,
   722                                                                         body={}))
   723                                           
   724                                                   helpers.change_label(self, 'cblabel', value, '_gcp_image', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 761

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   761                                               @profile
   762                                               def refresh(self):
   763                                                   """
   764                                                   Refreshes the state of this instance by re-querying the cloud provider
   765                                                   for its latest state.
   766                                                   """
   767                                                   image = self._provider.compute.images.get(self.id)
   768                                                   if image:
   769                                                       # pylint:disable=protected-access
   770                                                       self._gcp_image = image._gcp_image
   771                                                   else:
   772                                                       # image no longer exists
   773                                                       self._gcp_image['status'] = MachineImageState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 822

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   822                                               @label.setter
   823                                               # pylint:disable=arguments-differ
   824                                               @profile
   825                                               def label(self, value):
   826                                                   req = (self._provider
   827                                                              .gcp_compute
   828                                                              .instances()
   829                                                              .setLabels(project=self._provider.project_name,
   830                                                                         zone=self.zone_name,
   831                                                                         instance=self.name,
   832                                                                         body={}))
   833                                           
   834                                                   helpers.change_label(self, 'cblabel', value, '_gcp_instance', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1237

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1237                                               @profile
  1238                                               def refresh(self):
  1239                                                   """
  1240                                                   Refreshes the state of this instance by re-querying the cloud provider
  1241                                                   for its latest state.
  1242                                                   """
  1243                                                   inst = self._provider.compute.instances.get(self.id)
  1244                                                   if inst:
  1245                                                       # pylint:disable=protected-access
  1246                                                       self._gcp_instance = inst._gcp_instance
  1247                                                   else:
  1248                                                       # instance no longer exists
  1249                                                       self._gcp_instance['status'] = InstanceState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 1305

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1305                                               @label.setter
  1306                                               @profile
  1307                                               def label(self, value):
  1308                                                   self.assert_valid_resource_label(value)
  1309                                                   tag_name = "_".join(["network", self.name, "label"])
  1310                                                   helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342                                                   net = self._provider.networking.networks.get(self.id)
  1343                                                   if net:
  1344                                                       # pylint:disable=protected-access
  1345                                                       self._network = net._network
  1346                                                   else:
  1347                                                       # network no longer exists
  1348                                                       self._network['status'] = NetworkState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1390

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1390                                               @profile
  1391                                               def refresh(self):
  1392                                                   # pylint:disable=protected-access
  1393                                                   fip = self._provider.networking._floating_ips.get(None, self.id)
  1394                                                   # pylint:disable=protected-access
  1395                                                   self._ip = fip._ip
  1396                                                   self._process_ip_users()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 1445

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1445                                               @label.setter
  1446                                               @profile
  1447                                               def label(self, value):
  1448                                                   self.assert_valid_resource_label(value)
  1449                                                   tag_name = "_".join(["router", self.name, "label"])
  1450                                                   helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1457

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1457                                               @profile
  1458                                               def refresh(self):
  1459                                                   router = self._provider.networking.routers.get(self.id)
  1460                                                   if router:
  1461                                                       # pylint:disable=protected-access
  1462                                                       self._router = router._router
  1463                                                   else:
  1464                                                       # router no longer exists
  1465                                                       self._router['status'] = RouterState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1523

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1523                                               @profile
  1524                                               def refresh(self):
  1525                                                   pass

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 1565

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1565                                               @label.setter
  1566                                               @profile
  1567                                               def label(self, value):
  1568                                                   self.assert_valid_resource_label(value)
  1569                                                   tag_name = "_".join(["subnet", self.name, "label"])
  1570                                                   helpers.modify_or_add_metadata_item(self._provider, tag_name, value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1603

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1603                                               @profile
  1604                                               def refresh(self):
  1605                                                   subnet = self._provider.networking.subnets.get(self.id)
  1606                                                   if subnet:
  1607                                                       # pylint:disable=protected-access
  1608                                                       self._subnet = subnet._subnet
  1609                                                   else:
  1610                                                       # subnet no longer exists
  1611                                                       self._subnet['status'] = SubnetState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 1643

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1643                                               @label.setter
  1644                                               @profile
  1645                                               def label(self, value):
  1646                                                   req = (self._provider
  1647                                                              .gcp_compute
  1648                                                              .disks()
  1649                                                              .setLabels(project=self._provider.project_name,
  1650                                                                         zone=self.zone_name,
  1651                                                                         resource=self.name,
  1652                                                                         body={}))
  1653                                           
  1654                                                   helpers.change_label(self, 'cblabel', value, '_volume', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: description at line 1663

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1663                                               @description.setter
  1664                                               @profile
  1665                                               def description(self, value):
  1666                                                   req = (self._provider
  1667                                                          .gcp_compute
  1668                                                          .disks()
  1669                                                          .setLabels(project=self._provider.project_name,
  1670                                                                     zone=self.zone_name,
  1671                                                                     resource=self.name,
  1672                                                                     body={}))
  1673                                           
  1674                                                   helpers.change_label(self, 'description', value, '_volume', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1789

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1789                                               @profile
  1790                                               def refresh(self):
  1791                                                   """
  1792                                                   Refreshes the state of this volume by re-querying the cloud provider
  1793                                                   for its latest state.
  1794                                                   """
  1795                                                   vol = self._provider.storage.volumes.get(self.id)
  1796                                                   if vol:
  1797                                                       # pylint:disable=protected-access
  1798                                                       self._volume = vol._volume
  1799                                                   else:
  1800                                                       # volume no longer exists
  1801                                                       self._volume['status'] = VolumeState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: label at line 1831

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1831                                               @label.setter
  1832                                               # pylint:disable=arguments-differ
  1833                                               @profile
  1834                                               def label(self, value):
  1835                                                   req = (self._provider
  1836                                                              .gcp_compute
  1837                                                              .snapshots()
  1838                                                              .setLabels(project=self._provider.project_name,
  1839                                                                         resource=self.name,
  1840                                                                         body={}))
  1841                                           
  1842                                                   helpers.change_label(self, 'cblabel', value, '_snapshot', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: description at line 1851

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1851                                               @description.setter
  1852                                               @profile
  1853                                               def description(self, value):
  1854                                                   req = (self._provider
  1855                                                          .gcp_compute
  1856                                                          .snapshots()
  1857                                                          .setLabels(project=self._provider.project_name,
  1858                                                                     resource=self.name,
  1859                                                                     body={}))
  1860                                           
  1861                                                   helpers.change_label(self, 'description', value, '_snapshot', req)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 1880

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1880                                               @profile
  1881                                               def refresh(self):
  1882                                                   """
  1883                                                   Refreshes the state of this snapshot by re-querying the cloud provider
  1884                                                   for its latest state.
  1885                                                   """
  1886                                                   snap = self._provider.storage.snapshots.get(self.id)
  1887                                                   if snap:
  1888                                                       # pylint:disable=protected-access
  1889                                                       self._snapshot = snap._snapshot
  1890                                                   else:
  1891                                                       # snapshot no longer exists
  1892                                                       self._snapshot['status'] = SnapshotState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/resources.py
Function: refresh at line 2018

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  2018                                               @profile
  2019                                               def refresh(self):
  2020                                                   # pylint:disable=protected-access
  2021                                                   self._obj = self.bucket.objects.get(self.id)._obj

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
    98                                                   for kp in self:
    99                                                       if kp.id == key_pair_id:
   100                                                           return kp
   101                                                   else:
   102                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 104

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   104                                               @dispatch(event="provider.security.key_pairs.list",
   105                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   106                                               @profile
   107                                               def list(self, limit=None, marker=None):
   108                                                   key_pairs = []
   109                                                   for item in helpers.find_matching_metadata_items(
   110                                                           self.provider, GCPKeyPair.KP_TAG_REGEX):
   111                                                       metadata_value = json.loads(item['value'])
   112                                                       kp_info = GCPKeyPair.GCPKeyInfo(**metadata_value)
   113                                                       key_pairs.append(GCPKeyPair(self.provider, kp_info))
   114                                                   return ClientPagedResultList(self.provider, key_pairs,
   115                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
   124                                                   obj_list = self
   125                                                   filters = ['id', 'name']
   126                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   127                                           
   128                                                   # All kwargs should have been popped at this time.
   129                                                   if len(kwargs) > 0:
   130                                                       raise InvalidParamException(
   131                                                           "Unrecognised parameters for search: %s. Supported "
   132                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   133                                           
   134                                                   return ClientPagedResultList(self.provider,
   135                                                                                matches if matches else [])

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 137

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   137                                               @dispatch(event="provider.security.key_pairs.create",
   138                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   139                                               @profile
   140                                               def create(self, name, public_key_material=None):
   141                                                   GCPKeyPair.assert_valid_resource_name(name)
   142                                                   private_key = None
   143                                                   if not public_key_material:
   144                                                       public_key_material, private_key = cb_helpers.generate_key_pair()
   145                                                   # TODO: Add support for other formats not assume ssh-rsa
   146                                                   elif "ssh-rsa" not in public_key_material:
   147                                                       public_key_material = "ssh-rsa {}".format(public_key_material)
   148                                                   kp_info = GCPKeyPair.GCPKeyInfo(name, public_key_material)
   149                                                   metadata_value = json.dumps(kp_info._asdict())
   150                                                   try:
   151                                                       helpers.add_metadata_item(self.provider,
   152                                                                                 GCPKeyPair.KP_TAG_PREFIX + name,
   153                                                                                 metadata_value)
   154                                                       return GCPKeyPair(self.provider, kp_info, private_key)
   155                                                   except googleapiclient.errors.HttpError as err:
   156                                                       if err.resp.get('content-type', '').startswith('application/json'):
   157                                                           message = (json.loads(err.content).get('error', {})
   158                                                                      .get('errors', [{}])[0].get('message'))
   159                                                           if "duplicate keys" in message:
   160                                                               raise DuplicateResourceException(
   161                                                                   'A KeyPair with name {0} already exists'.format(name))
   162                                                       raise

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 164

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   164                                               @dispatch(event="provider.security.key_pairs.delete",
   165                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   166                                               @profile
   167                                               def delete(self, key_pair):
   168                                                   key_pair = (key_pair if isinstance(key_pair, GCPKeyPair) else
   169                                                               self.get(key_pair))
   170                                                   if key_pair:
   171                                                       helpers.remove_metadata_item(
   172                                                           self.provider, GCPKeyPair.KP_TAG_PREFIX + key_pair.name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 181

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   181                                               @dispatch(event="provider.security.vm_firewalls.get",
   182                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   183                                               @profile
   184                                               def get(self, vm_firewall_id):
   185                                                   tag, network_name = \
   186                                                       self._delegate.get_tag_network_from_id(vm_firewall_id)
   187                                                   if tag is None:
   188                                                       return None
   189                                                   network = self.provider.networking.networks.get(network_name)
   190                                                   return GCPVMFirewall(self._delegate, tag, network)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 192

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   192                                               @dispatch(event="provider.security.vm_firewalls.list",
   193                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   194                                               @profile
   195                                               def list(self, limit=None, marker=None):
   196                                                   vm_firewalls = []
   197                                                   for tag, network_name in self._delegate.tag_networks:
   198                                                       network = self.provider.networking.networks.get(
   199                                                               network_name)
   200                                                       vm_firewall = GCPVMFirewall(self._delegate, tag, network)
   201                                                       vm_firewalls.append(vm_firewall)
   202                                                   return ClientPagedResultList(self.provider, vm_firewalls,
   203                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 205

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   205                                               @dispatch(event="provider.security.vm_firewalls.create",
   206                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   207                                               @profile
   208                                               def create(self, label, network, description=None):
   209                                                   GCPVMFirewall.assert_valid_resource_label(label)
   210                                                   network = (network if isinstance(network, GCPNetwork)
   211                                                              else self.provider.networking.networks.get(network))
   212                                                   fw = GCPVMFirewall(self._delegate, label, network, description)
   213                                                   fw.label = label
   214                                                   # This rule exists implicitly. Add it explicitly so that the firewall
   215                                                   # is not empty and the rule is shown by list/get/find methods.
   216                                                   # pylint:disable=protected-access
   217                                                   self.provider.security._vm_firewall_rules.create_with_priority(
   218                                                       fw, direction=TrafficDirection.OUTBOUND, protocol='tcp',
   219                                                       priority=65534, cidr='0.0.0.0/0')
   220                                                   return fw

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 222

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   222                                               @dispatch(event="provider.security.vm_firewalls.delete",
   223                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   224                                               @profile
   225                                               def delete(self, vm_firewall):
   226                                                   fw_id = (vm_firewall.id if isinstance(vm_firewall, GCPVMFirewall)
   227                                                            else vm_firewall)
   228                                                   return self._delegate.delete_tag_network_with_id(fw_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find_by_network_and_tags at line 230

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   230                                               @profile
   231                                               def find_by_network_and_tags(self, network_name, tags):
   232                                                   """
   233                                                   Finds non-empty VM firewalls by network name and VM firewall names
   234                                                   (tags). If no matching VM firewall is found, an empty list is returned.
   235                                                   """
   236                                                   vm_firewalls = []
   237                                                   for tag, net_name in self._delegate.tag_networks:
   238                                                       if network_name != net_name:
   239                                                           continue
   240                                                       if tag not in tags:
   241                                                           continue
   242                                                       network = self.provider.networking.networks.get(net_name)
   243                                                       vm_firewalls.append(
   244                                                           GCPVMFirewall(self._delegate, tag, network))
   245                                                   return vm_firewalls

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 254

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   254                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   255                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   256                                               @profile
   257                                               def list(self, firewall, limit=None, marker=None):
   258                                                   rules = []
   259                                                   for fw in firewall.delegate.iter_firewalls(
   260                                                           firewall.name, firewall.network.name):
   261                                                       rule = GCPVMFirewallRule(firewall, fw['id'])
   262                                                       if rule.is_dummy_rule():
   263                                                           self._dummy_rule = rule
   264                                                       else:
   265                                                           rules.append(rule)
   266                                                   return ClientPagedResultList(self.provider, rules,
   267                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create_with_priority at line 284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   284                                               @profile
   285                                               def create_with_priority(self, firewall, direction, protocol, priority,
   286                                                                        from_port=None, to_port=None, cidr=None,
   287                                                                        src_dest_fw=None):
   288                                                   port = GCPVMFirewallRuleService.to_port_range(from_port, to_port)
   289                                                   src_dest_tag = None
   290                                                   src_dest_fw_id = None
   291                                                   if src_dest_fw:
   292                                                       src_dest_tag = src_dest_fw.name
   293                                                       src_dest_fw_id = src_dest_fw.id
   294                                                   if not firewall.delegate.add_firewall(
   295                                                           firewall.name, direction, protocol, priority, port, cidr,
   296                                                           src_dest_tag, firewall.description,
   297                                                           firewall.network.name):
   298                                                       return None
   299                                                   rules = self.find(firewall, direction=direction, protocol=protocol,
   300                                                                     from_port=from_port, to_port=to_port, cidr=cidr,
   301                                                                     src_dest_fw_id=src_dest_fw_id)
   302                                                   if len(rules) < 1:
   303                                                       return None
   304                                                   return rules[0]

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   307                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, firewall, direction, protocol, from_port=None,
   310                                                          to_port=None, cidr=None, src_dest_fw=None):
   311                                                   return self.create_with_priority(firewall, direction, protocol,
   312                                                                                    1000, from_port, to_port, cidr,
   313                                                                                    src_dest_fw)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 315

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   315                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   316                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   317                                               @profile
   318                                               def delete(self, firewall, rule):
   319                                                   rule = (rule if isinstance(rule, GCPVMFirewallRule)
   320                                                           else self.get(firewall, rule))
   321                                                   if rule.is_dummy_rule():
   322                                                       return True
   323                                                   firewall.delegate.delete_firewall_id(rule._rule)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @dispatch(event="provider.compute.vm_types.get",
   342                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   343                                               @profile
   344                                               def get(self, vm_type_id):
   345                                                   vm_type = self.provider.get_resource('machineTypes', vm_type_id)
   346                                                   return GCPVMType(self.provider, vm_type) if vm_type else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 348

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   348                                               @dispatch(event="provider.compute.vm_types.find",
   349                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   350                                               @profile
   351                                               def find(self, **kwargs):
   352                                                   matched_inst_types = []
   353                                                   for inst_type in self.instance_data:
   354                                                       is_match = True
   355                                                       for key, value in kwargs.items():
   356                                                           if key not in inst_type:
   357                                                               raise InvalidParamException(
   358                                                                   "Unrecognised parameters for search: %s." % key)
   359                                                           if inst_type.get(key) != value:
   360                                                               is_match = False
   361                                                               break
   362                                                       if is_match:
   363                                                           matched_inst_types.append(
   364                                                               GCPVMType(self.provider, inst_type))
   365                                                   return matched_inst_types

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 367

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   367                                               @dispatch(event="provider.compute.vm_types.list",
   368                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   369                                               @profile
   370                                               def list(self, limit=None, marker=None):
   371                                                   inst_types = [GCPVMType(self.provider, inst_type)
   372                                                                 for inst_type in self.instance_data]
   373                                                   return ClientPagedResultList(self.provider, inst_types,
   374                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386                                                   region = self.provider.get_resource('regions', region_id,
   387                                                                                       region=region_id)
   388                                                   return GCPRegion(self.provider, region) if region else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 390

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   390                                               @dispatch(event="provider.compute.regions.list",
   391                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   392                                               @profile
   393                                               def list(self, limit=None, marker=None):
   394                                                   max_result = limit if limit is not None and limit < 500 else 500
   395                                                   regions_response = (self.provider
   396                                                                           .gcp_compute
   397                                                                           .regions()
   398                                                                           .list(project=self.provider.project_name,
   399                                                                                 maxResults=max_result,
   400                                                                                 pageToken=marker)
   401                                                                           .execute())
   402                                                   regions = [GCPRegion(self.provider, region)
   403                                                              for region in regions_response['items']]
   404                                                   if len(regions) > max_result:
   405                                                       log.warning('Expected at most %d results; got %d',
   406                                                                   max_result, len(regions))
   407                                                   return ServerPagedResultList('nextPageToken' in regions_response,
   408                                                                                regions_response.get('nextPageToken'),
   409                                                                                False, data=regions)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 435

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   435                                               @profile
   436                                               def get(self, image_id):
   437                                                   """
   438                                                   Returns an Image given its id
   439                                                   """
   440                                                   image = self.provider.get_resource('images', image_id)
   441                                                   if image:
   442                                                       return GCPMachineImage(self.provider, image)
   443                                                   self._retrieve_public_images()
   444                                                   for public_image in self._public_images:
   445                                                       if public_image.id == image_id or public_image.name == image_id:
   446                                                           return public_image
   447                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 449

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   449                                               @profile
   450                                               def find(self, limit=None, marker=None, **kwargs):
   451                                                   """
   452                                                   Searches for an image by a given list of attributes
   453                                                   """
   454                                                   label = kwargs.pop('label', None)
   455                                           
   456                                                   # All kwargs should have been popped at this time.
   457                                                   if len(kwargs) > 0:
   458                                                       raise InvalidParamException(
   459                                                           "Unrecognised parameters for search: %s. Supported "
   460                                                           "attributes: %s" % (kwargs, 'label'))
   461                                           
   462                                                   # Retrieve all available images by setting limit to sys.maxsize
   463                                                   images = [image for image in self if image.label == label]
   464                                                   return ClientPagedResultList(self.provider, images,
   465                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 467

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   467                                               @profile
   468                                               def list(self, limit=None, marker=None):
   469                                                   """
   470                                                   List all images.
   471                                                   """
   472                                                   self._retrieve_public_images()
   473                                                   images = []
   474                                                   if (self.provider.project_name not in
   475                                                           GCPImageService._PUBLIC_IMAGE_PROJECTS):
   476                                                       for image in helpers.iter_all(
   477                                                               self.provider.gcp_compute.images(),
   478                                                               project=self.provider.project_name):
   479                                                           images.append(GCPMachineImage(self.provider, image))
   480                                                   images.extend(self._public_images)
   481                                                   return ClientPagedResultList(self.provider, images,
   482                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 490

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   490                                               @dispatch(event="provider.compute.instances.create",
   491                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   492                                               @profile
   493                                               def create(self, label, image, vm_type, subnet, zone=None,
   494                                                          key_pair=None, vm_firewalls=None, user_data=None,
   495                                                          launch_config=None, **kwargs):
   496                                                   """
   497                                                   Creates a new virtual machine instance.
   498                                                   """
   499                                                   GCPInstance.assert_valid_resource_name(label)
   500                                                   zone_name = self.provider.default_zone
   501                                                   if zone:
   502                                                       if not isinstance(zone, GCPPlacementZone):
   503                                                           zone = GCPPlacementZone(
   504                                                               self.provider,
   505                                                               self.provider.get_resource('zones', zone))
   506                                                       zone_name = zone.name
   507                                                   if not isinstance(vm_type, GCPVMType):
   508                                                       vm_type = self.provider.compute.vm_types.get(vm_type)
   509                                           
   510                                                   network_interface = {'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
   511                                                                                           'name': 'External NAT'}]}
   512                                                   if subnet:
   513                                                       network_interface['subnetwork'] = subnet.id
   514                                                   else:
   515                                                       network_interface['network'] = 'global/networks/default'
   516                                           
   517                                                   num_roots = 0
   518                                                   disks = []
   519                                                   boot_disk = None
   520                                                   if isinstance(launch_config, GCPLaunchConfig):
   521                                                       for disk in launch_config.block_devices:
   522                                                           if not disk.source:
   523                                                               volume_name = 'disk-{0}'.format(uuid.uuid4())
   524                                                               volume_size = disk.size if disk.size else 1
   525                                                               volume = self.provider.storage.volumes.create(
   526                                                                   volume_name, volume_size, zone)
   527                                                               volume.wait_till_ready()
   528                                                               source_field = 'source'
   529                                                               source_value = volume.id
   530                                                           elif isinstance(disk.source, GCPMachineImage):
   531                                                               source_field = 'initializeParams'
   532                                                               # Explicitly set diskName; otherwise, instance label will
   533                                                               # be used by default which may collide with existing disks.
   534                                                               source_value = {
   535                                                                   'sourceImage': disk.source.id,
   536                                                                   'diskName': 'image-disk-{0}'.format(uuid.uuid4()),
   537                                                                   'diskSizeGb': disk.size if disk.size else 20}
   538                                                           elif isinstance(disk.source, GCPVolume):
   539                                                               source_field = 'source'
   540                                                               source_value = disk.source.id
   541                                                           elif isinstance(disk.source, GCPSnapshot):
   542                                                               volume = disk.source.create_volume(zone, size=disk.size)
   543                                                               volume.wait_till_ready()
   544                                                               source_field = 'source'
   545                                                               source_value = volume.id
   546                                                           else:
   547                                                               log.warning('Unknown disk source')
   548                                                               continue
   549                                                           autoDelete = True
   550                                                           if disk.delete_on_terminate is not None:
   551                                                               autoDelete = disk.delete_on_terminate
   552                                                           num_roots += 1 if disk.is_root else 0
   553                                                           if disk.is_root and not boot_disk:
   554                                                               boot_disk = {'boot': True,
   555                                                                            'autoDelete': autoDelete,
   556                                                                            source_field: source_value}
   557                                                           else:
   558                                                               disks.append({'boot': False,
   559                                                                             'autoDelete': autoDelete,
   560                                                                             source_field: source_value})
   561                                           
   562                                                   if num_roots > 1:
   563                                                       log.warning('The launch config contains %d boot disks. Will '
   564                                                                   'use the first one', num_roots)
   565                                                   if image:
   566                                                       if boot_disk:
   567                                                           log.warning('A boot image is given while the launch config '
   568                                                                       'contains a boot disk, too. The launch config '
   569                                                                       'will be used.')
   570                                                       else:
   571                                                           if not isinstance(image, GCPMachineImage):
   572                                                               image = self.provider.compute.images.get(image)
   573                                                           # Explicitly set diskName; otherwise, instance name will be
   574                                                           # used by default which may conflict with existing disks.
   575                                                           boot_disk = {
   576                                                               'boot': True,
   577                                                               'autoDelete': True,
   578                                                               'initializeParams': {
   579                                                                   'sourceImage': image.id,
   580                                                                   'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}
   581                                           
   582                                                   if not boot_disk:
   583                                                       log.warning('No boot disk is given for instance %s.', label)
   584                                                       return None
   585                                                   # The boot disk must be the first disk attached to the instance.
   586                                                   disks.insert(0, boot_disk)
   587                                           
   588                                                   config = {
   589                                                       'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
   590                                                       'machineType': vm_type.resource_url,
   591                                                       'disks': disks,
   592                                                       'networkInterfaces': [network_interface]
   593                                                   }
   594                                           
   595                                                   if vm_firewalls and isinstance(vm_firewalls, list):
   596                                                       vm_firewall_names = []
   597                                                       if isinstance(vm_firewalls[0], VMFirewall):
   598                                                           vm_firewall_names = [f.name for f in vm_firewalls]
   599                                                       elif isinstance(vm_firewalls[0], str):
   600                                                           vm_firewall_names = vm_firewalls
   601                                                       if len(vm_firewall_names) > 0:
   602                                                           config['tags'] = {}
   603                                                           config['tags']['items'] = vm_firewall_names
   604                                           
   605                                                   if user_data:
   606                                                       entry = {'key': 'user-data', 'value': user_data}
   607                                                       config['metadata'] = {'items': [entry]}
   608                                           
   609                                                   if key_pair:
   610                                                       if not isinstance(key_pair, GCPKeyPair):
   611                                                           key_pair = self._provider.security.key_pairs.get(key_pair)
   612                                                       if key_pair:
   613                                                           kp = key_pair._key_pair
   614                                                           kp_entry = {
   615                                                               "key": "ssh-keys",
   616                                                               # Format is not removed from public key portion
   617                                                               "value": "{}:{} {}".format(
   618                                                                   self.provider.vm_default_user_name,
   619                                                                   kp.public_key,
   620                                                                   kp.name)
   621                                                               }
   622                                                           meta = config.get('metadata', {})
   623                                                           if meta:
   624                                                               items = meta.get('items', [])
   625                                                               items.append(kp_entry)
   626                                                           else:
   627                                                               config['metadata'] = {'items': [kp_entry]}
   628                                           
   629                                                   config['labels'] = {'cblabel': label}
   630                                           
   631                                                   operation = (self.provider
   632                                                                    .gcp_compute.instances()
   633                                                                    .insert(project=self.provider.project_name,
   634                                                                            zone=zone_name,
   635                                                                            body=config)
   636                                                                    .execute())
   637                                                   instance_id = operation.get('targetLink')
   638                                                   self.provider.wait_for_operation(operation, zone=zone_name)
   639                                                   cb_inst = self.get(instance_id)
   640                                                   return cb_inst

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 642

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   642                                               @dispatch(event="provider.compute.instances.get",
   643                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   644                                               @profile
   645                                               def get(self, instance_id):
   646                                                   """
   647                                                   Returns an instance given its name. Returns None
   648                                                   if the object does not exist.
   649                                           
   650                                                   A GCP instance is uniquely identified by its selfLink, which is used
   651                                                   as its id.
   652                                                   """
   653                                                   instance = self.provider.get_resource('instances', instance_id)
   654                                                   return GCPInstance(self.provider, instance) if instance else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 656

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   656                                               @dispatch(event="provider.compute.instances.find",
   657                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   658                                               @profile
   659                                               def find(self, limit=None, marker=None, **kwargs):
   660                                                   """
   661                                                   Searches for instances by instance label.
   662                                                   :return: a list of Instance objects
   663                                                   """
   664                                                   label = kwargs.pop('label', None)
   665                                           
   666                                                   # All kwargs should have been popped at this time.
   667                                                   if len(kwargs) > 0:
   668                                                       raise InvalidParamException(
   669                                                           "Unrecognised parameters for search: %s. Supported "
   670                                                           "attributes: %s" % (kwargs, 'label'))
   671                                           
   672                                                   instances = [instance for instance in self.list()
   673                                                                if instance.label == label]
   674                                                   return ClientPagedResultList(self.provider, instances,
   675                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @dispatch(event="provider.compute.instances.list",
   678                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   679                                               @profile
   680                                               def list(self, limit=None, marker=None):
   681                                                   """
   682                                                   List all instances.
   683                                                   """
   684                                                   # For GCP API, Acceptable values are 0 to 500, inclusive.
   685                                                   # (Default: 500).
   686                                                   max_result = limit if limit is not None and limit < 500 else 500
   687                                                   response = (self.provider
   688                                                                   .gcp_compute
   689                                                                   .instances()
   690                                                                   .list(project=self.provider.project_name,
   691                                                                         zone=self.provider.default_zone,
   692                                                                         maxResults=max_result,
   693                                                                         pageToken=marker)
   694                                                                   .execute())
   695                                                   instances = [GCPInstance(self.provider, inst)
   696                                                                for inst in response.get('items', [])]
   697                                                   if len(instances) > max_result:
   698                                                       log.warning('Expected at most %d results; got %d',
   699                                                                   max_result, len(instances))
   700                                                   return ServerPagedResultList('nextPageToken' in response,
   701                                                                                response.get('nextPageToken'),
   702                                                                                False, data=instances)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 704

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   704                                               @dispatch(event="provider.compute.instances.delete",
   705                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   706                                               @profile
   707                                               def delete(self, instance):
   708                                                   instance = (instance if isinstance(instance, GCPInstance) else
   709                                                               self.get(instance))
   710                                                   if instance:
   711                                                       (self._provider
   712                                                        .gcp_compute
   713                                                        .instances()
   714                                                        .delete(project=self.provider.project_name,
   715                                                                zone=instance.zone_name,
   716                                                                instance=instance.name)
   717                                                        .execute())

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create_launch_config at line 719

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   719                                               @profile
   720                                               def create_launch_config(self):
   721                                                   return GCPLaunchConfig(self.provider)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 786

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   786                                               @dispatch(event="provider.networking.networks.get",
   787                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   788                                               @profile
   789                                               def get(self, network_id):
   790                                                   network = self.provider.get_resource('networks', network_id)
   791                                                   return GCPNetwork(self.provider, network) if network else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
   801                                                   obj_list = self
   802                                                   filters = ['name', 'label']
   803                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   804                                                   return ClientPagedResultList(self._provider, list(matches),
   805                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 807

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   807                                               @dispatch(event="provider.networking.networks.list",
   808                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   809                                               @profile
   810                                               def list(self, limit=None, marker=None, filter=None):
   811                                                   # TODO: Decide whether we keep filter in 'list'
   812                                                   networks = []
   813                                                   response = (self.provider
   814                                                                   .gcp_compute
   815                                                                   .networks()
   816                                                                   .list(project=self.provider.project_name,
   817                                                                         filter=filter)
   818                                                                   .execute())
   819                                                   for network in response.get('items', []):
   820                                                       networks.append(GCPNetwork(self.provider, network))
   821                                                   return ClientPagedResultList(self.provider, networks,
   822                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
   832                                                   GCPNetwork.assert_valid_resource_label(label)
   833                                                   name = GCPNetwork._generate_name_from_label(label, 'cbnet')
   834                                                   body = {'name': name}
   835                                                   # This results in a custom mode network
   836                                                   body['autoCreateSubnetworks'] = False
   837                                                   response = (self.provider
   838                                                                   .gcp_compute
   839                                                                   .networks()
   840                                                                   .insert(project=self.provider.project_name,
   841                                                                           body=body)
   842                                                                   .execute())
   843                                                   self.provider.wait_for_operation(response)
   844                                                   cb_net = self.get(name)
   845                                                   cb_net.label = label
   846                                                   return cb_net

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get_or_create_default at line 848

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   848                                               @profile
   849                                               def get_or_create_default(self):
   850                                                   default_nets = self.provider.networking.networks.find(
   851                                                       label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
   852                                                   if default_nets:
   853                                                       return default_nets[0]
   854                                                   else:
   855                                                       log.info("Creating a CloudBridge-default network labeled %s",
   856                                                                GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
   857                                                       return self.create(
   858                                                           label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL,
   859                                                           cidr_block=GCPNetwork.CB_DEFAULT_IPV4RANGE)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 861

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   861                                               @dispatch(event="provider.networking.networks.delete",
   862                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   863                                               @profile
   864                                               def delete(self, network):
   865                                                   # Accepts network object
   866                                                   if isinstance(network, GCPNetwork):
   867                                                       name = network.name
   868                                                   # Accepts both name and ID
   869                                                   elif 'googleapis' in network:
   870                                                       name = network.split('/')[-1]
   871                                                   else:
   872                                                       name = network
   873                                                   response = (self.provider
   874                                                                   .gcp_compute
   875                                                                   .networks()
   876                                                                   .delete(project=self.provider.project_name,
   877                                                                           network=name)
   878                                                                   .execute())
   879                                                   self.provider.wait_for_operation(response)
   880                                                   # Remove label
   881                                                   tag_name = "_".join(["network", name, "label"])
   882                                                   if not helpers.remove_metadata_item(self.provider, tag_name):
   883                                                       log.warning('No label was found associated with this network '
   884                                                                   '"{}" when deleted.'.format(network))
   885                                                   return True

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 893

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   893                                               @dispatch(event="provider.networking.routers.get",
   894                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   895                                               @profile
   896                                               def get(self, router_id):
   897                                                   router = self.provider.get_resource(
   898                                                       'routers', router_id, region=self.provider.region_name)
   899                                                   return GCPRouter(self.provider, router) if router else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 901

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   901                                               @dispatch(event="provider.networking.routers.find",
   902                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   903                                               @profile
   904                                               def find(self, limit=None, marker=None, **kwargs):
   905                                                   obj_list = self
   906                                                   filters = ['name', 'label']
   907                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   908                                                   return ClientPagedResultList(self._provider, list(matches),
   909                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 911

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   911                                               @dispatch(event="provider.networking.routers.list",
   912                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   913                                               @profile
   914                                               def list(self, limit=None, marker=None):
   915                                                   region = self.provider.region_name
   916                                                   max_result = limit if limit is not None and limit < 500 else 500
   917                                                   response = (self.provider
   918                                                                   .gcp_compute
   919                                                                   .routers()
   920                                                                   .list(project=self.provider.project_name,
   921                                                                         region=region,
   922                                                                         maxResults=max_result,
   923                                                                         pageToken=marker)
   924                                                                   .execute())
   925                                                   routers = []
   926                                                   for router in response.get('items', []):
   927                                                       routers.append(GCPRouter(self.provider, router))
   928                                                   if len(routers) > max_result:
   929                                                       log.warning('Expected at most %d results; go %d',
   930                                                                   max_result, len(routers))
   931                                                   return ServerPagedResultList('nextPageToken' in response,
   932                                                                                response.get('nextPageToken'),
   933                                                                                False, data=routers)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 935

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   935                                               @dispatch(event="provider.networking.routers.create",
   936                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   937                                               @profile
   938                                               def create(self, label, network):
   939                                                   log.debug("Creating GCP Router Service with params "
   940                                                             "[label: %s network: %s]", label, network)
   941                                                   GCPRouter.assert_valid_resource_label(label)
   942                                                   name = GCPRouter._generate_name_from_label(label, 'cb-router')
   943                                           
   944                                                   if not isinstance(network, GCPNetwork):
   945                                                       network = self.provider.networking.networks.get(network)
   946                                                   network_url = network.resource_url
   947                                                   region_name = self.provider.region_name
   948                                                   response = (self.provider
   949                                                                   .gcp_compute
   950                                                                   .routers()
   951                                                                   .insert(project=self.provider.project_name,
   952                                                                           region=region_name,
   953                                                                           body={'name': name,
   954                                                                                 'network': network_url})
   955                                                                   .execute())
   956                                                   self.provider.wait_for_operation(response, region=region_name)
   957                                                   cb_router = self.get(name)
   958                                                   cb_router.label = label
   959                                                   return cb_router

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 961

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   961                                               @dispatch(event="provider.networking.routers.delete",
   962                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
   963                                               @profile
   964                                               def delete(self, router):
   965                                                   r = router if isinstance(router, GCPRouter) else self.get(router)
   966                                                   if r:
   967                                                       (self.provider
   968                                                        .gcp_compute
   969                                                        .routers()
   970                                                        .delete(project=self.provider.project_name,
   971                                                                region=r.region_name,
   972                                                                router=r.name)
   973                                                        .execute())
   974                                                       # Remove label
   975                                                       tag_name = "_".join(["router", r.name, "label"])
   976                                                       if not helpers.remove_metadata_item(self.provider, tag_name):
   977                                                           log.warning('No label was found associated with this router '
   978                                                                       '"{}" when deleted.'.format(r.name))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 996

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   996                                               @dispatch(event="provider.networking.subnets.get",
   997                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
   998                                               @profile
   999                                               def get(self, subnet_id):
  1000                                                   subnet = self.provider.get_resource('subnetworks', subnet_id)
  1001                                                   return GCPSubnet(self.provider, subnet) if subnet else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
  1010                                                   filter = None
  1011                                                   if network is not None:
  1012                                                       network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014                                                       filter = 'network eq %s' % network.resource_url
  1015                                                   if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018                                                       region_name = self.provider.region_name
  1019                                                   subnets = []
  1020                                                   response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023                                                                   .list(project=self.provider.project_name,
  1024                                                                         region=region_name,
  1025                                                                         filter=filter)
  1026                                                                   .execute())
  1027                                                   for subnet in response.get('items', []):
  1028                                                       subnets.append(GCPSubnet(self.provider, subnet))
  1029                                                   return ClientPagedResultList(self.provider, subnets,
  1030                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
  1045                                                   GCPSubnet.assert_valid_resource_label(label)
  1046                                                   name = GCPSubnet._generate_name_from_label(label, 'cbsubnet')
  1047                                                   region_name = self._zone_to_region(zone)
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
  1060                                                   body = {'ipCidrRange': cidr_block,
  1061                                                           'name': name,
  1062                                                           'network': network.resource_url,
  1063                                                           'region': region_name
  1064                                                           }
  1065                                                   response = (self.provider
  1066                                                                   .gcp_compute
  1067                                                                   .subnetworks()
  1068                                                                   .insert(project=self.provider.project_name,
  1069                                                                           region=region_name,
  1070                                                                           body=body)
  1071                                                                   .execute())
  1072                                                   self.provider.wait_for_operation(response, region=region_name)
  1073                                                   cb_subnet = self.get(name)
  1074                                                   cb_subnet.label = label
  1075                                                   return cb_subnet

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1077

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1077                                               @dispatch(event="provider.networking.subnets.delete",
  1078                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1079                                               @profile
  1080                                               def delete(self, subnet):
  1081                                                   sn = subnet if isinstance(subnet, GCPSubnet) else self.get(subnet)
  1082                                                   if not sn:
  1083                                                       return
  1084                                                   response = (self.provider
  1085                                                               .gcp_compute
  1086                                                               .subnetworks()
  1087                                                               .delete(project=self.provider.project_name,
  1088                                                                       region=sn.region_name,
  1089                                                                       subnetwork=sn.name)
  1090                                                               .execute())
  1091                                                   self.provider.wait_for_operation(response, region=sn.region_name)
  1092                                                   # Remove label
  1093                                                   tag_name = "_".join(["subnet", sn.name, "label"])
  1094                                                   if not helpers.remove_metadata_item(self._provider, tag_name):
  1095                                                       log.warning('No label was found associated with this subnet '
  1096                                                                   '"{}" when deleted.'.format(sn.name))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
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
  1108                                                   region = self._zone_to_region(zone or self.provider.default_zone,
  1109                                                                                 return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111                                                   for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112                                                       if sn.region == region.id:
  1113                                                           return sn
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

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 1196

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1196                                               @dispatch(event="provider.storage.volumes.get",
  1197                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1198                                               @profile
  1199                                               def get(self, volume_id):
  1200                                                   vol = self.provider.get_resource('disks', volume_id)
  1201                                                   return GCPVolume(self.provider, vol) if vol else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 1203

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1203                                               @dispatch(event="provider.storage.volumes.find",
  1204                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1205                                               @profile
  1206                                               def find(self, limit=None, marker=None, **kwargs):
  1207                                                   """
  1208                                                   Searches for a volume by a given list of attributes.
  1209                                                   """
  1210                                                   label = kwargs.pop('label', None)
  1211                                           
  1212                                                   # All kwargs should have been popped at this time.
  1213                                                   if len(kwargs) > 0:
  1214                                                       raise InvalidParamException(
  1215                                                           "Unrecognised parameters for search: %s. Supported "
  1216                                                           "attributes: %s" % (kwargs, 'label'))
  1217                                           
  1218                                                   filtr = 'labels.cblabel eq ' + label
  1219                                                   max_result = limit if limit is not None and limit < 500 else 500
  1220                                                   response = (self.provider
  1221                                                                   .gcp_compute
  1222                                                                   .disks()
  1223                                                                   .list(project=self.provider.project_name,
  1224                                                                         zone=self.provider.default_zone,
  1225                                                                         filter=filtr,
  1226                                                                         maxResults=max_result,
  1227                                                                         pageToken=marker)
  1228                                                                   .execute())
  1229                                                   gcp_vols = [GCPVolume(self.provider, vol)
  1230                                                               for vol in response.get('items', [])]
  1231                                                   if len(gcp_vols) > max_result:
  1232                                                       log.warning('Expected at most %d results; got %d',
  1233                                                                   max_result, len(gcp_vols))
  1234                                                   return ServerPagedResultList('nextPageToken' in response,
  1235                                                                                response.get('nextPageToken'),
  1236                                                                                False, data=gcp_vols)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1238

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1238                                               @dispatch(event="provider.storage.volumes.list",
  1239                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1240                                               @profile
  1241                                               def list(self, limit=None, marker=None):
  1242                                                   """
  1243                                                   List all volumes.
  1244                                           
  1245                                                   limit: The maximum number of volumes to return. The returned
  1246                                                          ResultList's is_truncated property can be used to determine
  1247                                                          whether more records are available.
  1248                                                   """
  1249                                                   # For GCP API, Acceptable values are 0 to 500, inclusive.
  1250                                                   # (Default: 500).
  1251                                                   max_result = limit if limit is not None and limit < 500 else 500
  1252                                                   response = (self.provider
  1253                                                                   .gcp_compute
  1254                                                                   .disks()
  1255                                                                   .list(project=self.provider.project_name,
  1256                                                                         zone=self.provider.default_zone,
  1257                                                                         maxResults=max_result,
  1258                                                                         pageToken=marker)
  1259                                                                   .execute())
  1260                                                   gcp_vols = [GCPVolume(self.provider, vol)
  1261                                                               for vol in response.get('items', [])]
  1262                                                   if len(gcp_vols) > max_result:
  1263                                                       log.warning('Expected at most %d results; got %d',
  1264                                                                   max_result, len(gcp_vols))
  1265                                                   return ServerPagedResultList('nextPageToken' in response,
  1266                                                                                response.get('nextPageToken'),
  1267                                                                                False, data=gcp_vols)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 1269

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1269                                               @dispatch(event="provider.storage.volumes.create",
  1270                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1271                                               @profile
  1272                                               def create(self, label, size, zone, snapshot=None, description=None):
  1273                                                   GCPVolume.assert_valid_resource_label(label)
  1274                                                   name = GCPVolume._generate_name_from_label(label, 'cb-vol')
  1275                                                   if not isinstance(zone, GCPPlacementZone):
  1276                                                       zone = GCPPlacementZone(
  1277                                                           self.provider,
  1278                                                           self.provider.get_resource('zones', zone))
  1279                                                   zone_name = zone.name
  1280                                                   snapshot_id = snapshot.id if isinstance(
  1281                                                       snapshot, GCPSnapshot) and snapshot else snapshot
  1282                                                   labels = {'cblabel': label}
  1283                                                   if description:
  1284                                                       labels['description'] = description
  1285                                                   disk_body = {
  1286                                                       'name': name,
  1287                                                       'sizeGb': size,
  1288                                                       'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
  1289                                                       'sourceSnapshot': snapshot_id,
  1290                                                       'labels': labels
  1291                                                   }
  1292                                                   operation = (self.provider
  1293                                                                    .gcp_compute
  1294                                                                    .disks()
  1295                                                                    .insert(
  1296                                                                        project=self._provider.project_name,
  1297                                                                        zone=zone_name,
  1298                                                                        body=disk_body)
  1299                                                                    .execute())
  1300                                                   cb_vol = self.get(operation.get('targetLink'))
  1301                                                   return cb_vol

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1303

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1303                                               @dispatch(event="provider.storage.volumes.delete",
  1304                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
  1305                                               @profile
  1306                                               def delete(self, volume):
  1307                                                   volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
  1308                                                   if volume:
  1309                                                       (self._provider.gcp_compute
  1310                                                                      .disks()
  1311                                                                      .delete(project=self.provider.project_name,
  1312                                                                              zone=volume.zone_name,
  1313                                                                              disk=volume.name)
  1314                                                                      .execute())

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 1322

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1322                                               @dispatch(event="provider.storage.snapshots.get",
  1323                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1324                                               @profile
  1325                                               def get(self, snapshot_id):
  1326                                                   snapshot = self.provider.get_resource('snapshots', snapshot_id)
  1327                                                   return GCPSnapshot(self.provider, snapshot) if snapshot else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 1329

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1329                                               @dispatch(event="provider.storage.snapshots.find",
  1330                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1331                                               @profile
  1332                                               def find(self, limit=None, marker=None, **kwargs):
  1333                                                   label = kwargs.pop('label', None)
  1334                                           
  1335                                                   # All kwargs should have been popped at this time.
  1336                                                   if len(kwargs) > 0:
  1337                                                       raise InvalidParamException(
  1338                                                           "Unrecognised parameters for search: %s. Supported "
  1339                                                           "attributes: %s" % (kwargs, 'label'))
  1340                                           
  1341                                                   filtr = 'labels.cblabel eq ' + label
  1342                                                   max_result = limit if limit is not None and limit < 500 else 500
  1343                                                   response = (self.provider
  1344                                                                   .gcp_compute
  1345                                                                   .snapshots()
  1346                                                                   .list(project=self.provider.project_name,
  1347                                                                         filter=filtr,
  1348                                                                         maxResults=max_result,
  1349                                                                         pageToken=marker)
  1350                                                                   .execute())
  1351                                                   snapshots = [GCPSnapshot(self.provider, snapshot)
  1352                                                                for snapshot in response.get('items', [])]
  1353                                                   if len(snapshots) > max_result:
  1354                                                       log.warning('Expected at most %d results; got %d',
  1355                                                                   max_result, len(snapshots))
  1356                                                   return ServerPagedResultList('nextPageToken' in response,
  1357                                                                                response.get('nextPageToken'),
  1358                                                                                False, data=snapshots)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1360

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1360                                               @dispatch(event="provider.storage.snapshots.list",
  1361                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1362                                               @profile
  1363                                               def list(self, limit=None, marker=None):
  1364                                                   max_result = limit if limit is not None and limit < 500 else 500
  1365                                                   response = (self.provider
  1366                                                                   .gcp_compute
  1367                                                                   .snapshots()
  1368                                                                   .list(project=self.provider.project_name,
  1369                                                                         maxResults=max_result,
  1370                                                                         pageToken=marker)
  1371                                                                   .execute())
  1372                                                   snapshots = [GCPSnapshot(self.provider, snapshot)
  1373                                                                for snapshot in response.get('items', [])]
  1374                                                   if len(snapshots) > max_result:
  1375                                                       log.warning('Expected at most %d results; got %d',
  1376                                                                   max_result, len(snapshots))
  1377                                                   return ServerPagedResultList('nextPageToken' in response,
  1378                                                                                response.get('nextPageToken'),
  1379                                                                                False, data=snapshots)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 1381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1381                                               @dispatch(event="provider.storage.snapshots.create",
  1382                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1383                                               @profile
  1384                                               def create(self, label, volume, description=None):
  1385                                                   GCPSnapshot.assert_valid_resource_label(label)
  1386                                                   name = GCPSnapshot._generate_name_from_label(label, 'cbsnap')
  1387                                                   volume_name = volume.name if isinstance(volume, GCPVolume) else volume
  1388                                                   labels = {'cblabel': label}
  1389                                                   if description:
  1390                                                       labels['description'] = description
  1391                                                   snapshot_body = {
  1392                                                       "name": name,
  1393                                                       "labels": labels
  1394                                                   }
  1395                                                   operation = (self.provider
  1396                                                                    .gcp_compute
  1397                                                                    .disks()
  1398                                                                    .createSnapshot(
  1399                                                                        project=self.provider.project_name,
  1400                                                                        zone=self.provider.default_zone,
  1401                                                                        disk=volume_name, body=snapshot_body)
  1402                                                                    .execute())
  1403                                                   if 'zone' not in operation:
  1404                                                       return None
  1405                                                   self.provider.wait_for_operation(operation,
  1406                                                                                    zone=self.provider.default_zone)
  1407                                                   cb_snap = self.get(name)
  1408                                                   return cb_snap

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1410

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1410                                               @dispatch(event="provider.storage.snapshots.delete",
  1411                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
  1412                                               @profile
  1413                                               def delete(self, snapshot):
  1414                                                   snapshot = (snapshot if isinstance(snapshot, GCPSnapshot)
  1415                                                               else self.get(snapshot))
  1416                                                   if snapshot:
  1417                                                       (self.provider
  1418                                                            .gcp_compute
  1419                                                            .snapshots()
  1420                                                            .delete(project=self.provider.project_name,
  1421                                                                    snapshot=snapshot.name)
  1422                                                            .execute())

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 1430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1430                                               @dispatch(event="provider.storage.buckets.get",
  1431                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1432                                               @profile
  1433                                               def get(self, bucket_id):
  1434                                                   """
  1435                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
  1436                                                   does not exist or if the user does not have permission to access the
  1437                                                   bucket.
  1438                                                   """
  1439                                                   bucket = self.provider.get_resource('buckets', bucket_id)
  1440                                                   return GCPBucket(self.provider, bucket) if bucket else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 1442

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1442                                               @dispatch(event="provider.storage.buckets.find",
  1443                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1444                                               @profile
  1445                                               def find(self, limit=None, marker=None, **kwargs):
  1446                                                   name = kwargs.pop('name', None)
  1447                                           
  1448                                                   # All kwargs should have been popped at this time.
  1449                                                   if len(kwargs) > 0:
  1450                                                       raise InvalidParamException(
  1451                                                           "Unrecognised parameters for search: %s. Supported "
  1452                                                           "attributes: %s" % (kwargs, 'name'))
  1453                                           
  1454                                                   buckets = [bucket for bucket in self if name in bucket.name]
  1455                                                   return ClientPagedResultList(self.provider, buckets, limit=limit,
  1456                                                                                marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1458

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1458                                               @dispatch(event="provider.storage.buckets.list",
  1459                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1460                                               @profile
  1461                                               def list(self, limit=None, marker=None):
  1462                                                   """
  1463                                                   List all containers.
  1464                                                   """
  1465                                                   max_result = limit if limit is not None and limit < 500 else 500
  1466                                                   response = (self.provider
  1467                                                                   .gcp_storage
  1468                                                                   .buckets()
  1469                                                                   .list(project=self.provider.project_name,
  1470                                                                         maxResults=max_result,
  1471                                                                         pageToken=marker)
  1472                                                                   .execute())
  1473                                                   buckets = []
  1474                                                   for bucket in response.get('items', []):
  1475                                                       buckets.append(GCPBucket(self.provider, bucket))
  1476                                                   if len(buckets) > max_result:
  1477                                                       log.warning('Expected at most %d results; got %d',
  1478                                                                   max_result, len(buckets))
  1479                                                   return ServerPagedResultList('nextPageToken' in response,
  1480                                                                                response.get('nextPageToken'),
  1481                                                                                False, data=buckets)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 1483

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1483                                               @dispatch(event="provider.storage.buckets.create",
  1484                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1485                                               @profile
  1486                                               def create(self, name, location=None):
  1487                                                   GCPBucket.assert_valid_resource_name(name)
  1488                                                   body = {'name': name}
  1489                                                   if location:
  1490                                                       body['location'] = location
  1491                                                   try:
  1492                                                       response = (self.provider
  1493                                                                       .gcp_storage
  1494                                                                       .buckets()
  1495                                                                       .insert(project=self.provider.project_name,
  1496                                                                               body=body)
  1497                                                                       .execute())
  1498                                                       # GCP has a rate limit of 1 operation per 2 seconds for bucket
  1499                                                       # creation/deletion: https://cloud.google.com/storage/quotas.
  1500                                                       # Throttle here to avoid future failures.
  1501                                                       time.sleep(2)
  1502                                                       return GCPBucket(self.provider, response)
  1503                                                   except googleapiclient.errors.HttpError as http_error:
  1504                                                       # 409 = conflict
  1505                                                       if http_error.resp.status in [409]:
  1506                                                           raise DuplicateResourceException(
  1507                                                               'Bucket already exists with name {0}'.format(name))
  1508                                                       else:
  1509                                                           raise

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1511

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1511                                               @dispatch(event="provider.storage.buckets.delete",
  1512                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
  1513                                               @profile
  1514                                               def delete(self, bucket):
  1515                                                   """
  1516                                                   Delete this bucket.
  1517                                                   """
  1518                                                   b = bucket if isinstance(bucket, GCPBucket) else self.get(bucket)
  1519                                                   if b:
  1520                                                       (self.provider
  1521                                                            .gcp_storage
  1522                                                            .buckets()
  1523                                                            .delete(bucket=b.name)
  1524                                                            .execute())
  1525                                                       # GCP has a rate limit of 1 operation per 2 seconds for bucket
  1526                                                       # creation/deletion: https://cloud.google.com/storage/quotas.
  1527                                                       # Throttle here to avoid future failures.
  1528                                                       time.sleep(2)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 1536

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1536                                               @profile
  1537                                               def get(self, bucket, name):
  1538                                                   """
  1539                                                   Retrieve a given object from this bucket.
  1540                                                   """
  1541                                                   obj = self.provider.get_resource('objects', name,
  1542                                                                                    bucket=bucket.name)
  1543                                                   return GCPBucketObject(self.provider, bucket, obj) if obj else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1545

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1545                                               @profile
  1546                                               def list(self, bucket, limit=None, marker=None, prefix=None):
  1547                                                   """
  1548                                                   List all objects within this bucket.
  1549                                                   """
  1550                                                   max_result = limit if limit is not None and limit < 500 else 500
  1551                                                   response = (self.provider
  1552                                                                   .gcp_storage
  1553                                                                   .objects()
  1554                                                                   .list(bucket=bucket.name,
  1555                                                                         prefix=prefix if prefix else '',
  1556                                                                         maxResults=max_result,
  1557                                                                         pageToken=marker)
  1558                                                                   .execute())
  1559                                                   objects = []
  1560                                                   for obj in response.get('items', []):
  1561                                                       objects.append(GCPBucketObject(self.provider, bucket, obj))
  1562                                                   if len(objects) > max_result:
  1563                                                       log.warning('Expected at most %d results; got %d',
  1564                                                                   max_result, len(objects))
  1565                                                   return ServerPagedResultList('nextPageToken' in response,
  1566                                                                                response.get('nextPageToken'),
  1567                                                                                False, data=objects)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: find at line 1569

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1569                                               @profile
  1570                                               def find(self, bucket, limit=None, marker=None, **kwargs):
  1571                                                   filters = ['name']
  1572                                                   matches = cb_helpers.generic_find(filters, kwargs, bucket.objects)
  1573                                                   return ClientPagedResultList(self._provider, list(matches),
  1574                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 1586

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1586                                               @profile
  1587                                               def create(self, bucket, name):
  1588                                                   response = self._create_object_with_media_body(
  1589                                                                       bucket,
  1590                                                                       name,
  1591                                                                       googleapiclient.http.MediaIoBaseUpload(
  1592                                                                           io.BytesIO(b''), mimetype='plain/text'))
  1593                                                   return GCPBucketObject(self._provider,
  1594                                                                          bucket,
  1595                                                                          response) if response else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get_or_create at line 1610

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1610                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1611                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1612                                               @profile
  1613                                               def get_or_create(self, network):
  1614                                                   return self._default_internet_gateway

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1616

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1616                                               @dispatch(event="provider.networking.gateways.delete",
  1617                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1618                                               @profile
  1619                                               def delete(self, network, gateway):
  1620                                                   pass

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1622

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1622                                               @dispatch(event="provider.networking.gateways.list",
  1623                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1624                                               @profile
  1625                                               def list(self, network, limit=None, marker=None):
  1626                                                   gws = [self._default_internet_gateway]
  1627                                                   return ClientPagedResultList(self._provider,
  1628                                                                                gws,
  1629                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: get at line 1637

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1637                                               @dispatch(event="provider.networking.floating_ips.get",
  1638                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1639                                               @profile
  1640                                               def get(self, gateway, floating_ip_id):
  1641                                                   fip = self.provider.get_resource('addresses', floating_ip_id)
  1642                                                   return (GCPFloatingIP(self.provider, fip)
  1643                                                           if fip else None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: list at line 1645

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1645                                               @dispatch(event="provider.networking.floating_ips.list",
  1646                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1647                                               @profile
  1648                                               def list(self, gateway, limit=None, marker=None):
  1649                                                   max_result = limit if limit is not None and limit < 500 else 500
  1650                                                   response = (self.provider
  1651                                                                   .gcp_compute
  1652                                                                   .addresses()
  1653                                                                   .list(project=self.provider.project_name,
  1654                                                                         region=self.provider.region_name,
  1655                                                                         maxResults=max_result,
  1656                                                                         pageToken=marker)
  1657                                                                   .execute())
  1658                                                   ips = [GCPFloatingIP(self.provider, ip)
  1659                                                          for ip in response.get('items', [])]
  1660                                                   if len(ips) > max_result:
  1661                                                       log.warning('Expected at most %d results; got %d',
  1662                                                                   max_result, len(ips))
  1663                                                   return ServerPagedResultList('nextPageToken' in response,
  1664                                                                                response.get('nextPageToken'),
  1665                                                                                False, data=ips)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: create at line 1667

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1667                                               @dispatch(event="provider.networking.floating_ips.create",
  1668                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1669                                               @profile
  1670                                               def create(self, gateway):
  1671                                                   region_name = self.provider.region_name
  1672                                                   ip_name = 'ip-{0}'.format(uuid.uuid4())
  1673                                                   response = (self.provider
  1674                                                               .gcp_compute
  1675                                                               .addresses()
  1676                                                               .insert(project=self.provider.project_name,
  1677                                                                       region=region_name,
  1678                                                                       body={'name': ip_name})
  1679                                                               .execute())
  1680                                                   self.provider.wait_for_operation(response, region=region_name)
  1681                                                   return self.get(gateway, ip_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/gcp/services.py
Function: delete at line 1683

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1683                                               @dispatch(event="provider.networking.floating_ips.delete",
  1684                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1685                                               @profile
  1686                                               def delete(self, gateway, fip):
  1687                                                   fip = (fip if isinstance(fip, GCPFloatingIP)
  1688                                                          else self.get(gateway, fip))
  1689                                                   project_name = self.provider.project_name
  1690                                                   # First, delete the forwarding rule, if there is any.
  1691                                                   # pylint:disable=protected-access
  1692                                                   if fip._rule:
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
  1704                                                   response = (self.provider
  1705                                                               .gcp_compute
  1706                                                               .addresses()
  1707                                                               .delete(project=project_name,
  1708                                                                       region=fip.region_name,
  1709                                                                       address=fip._ip['name'])
  1710                                                               .execute())
  1711                                                   self.provider.wait_for_operation(response,
  1712                                                                                    region=fip.region_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 108

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   108                                               @label.setter
   109                                               # pylint:disable=arguments-differ
   110                                               @profile
   111                                               def label(self, value):
   112                                                   """
   113                                                   Set the image label.
   114                                                   """
   115                                                   self.assert_valid_resource_label(value)
   116                                                   self._provider.os_conn.image.update_image(
   117                                                       self._os_image, name=value or "")

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 148

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   148                                               @profile
   149                                               def refresh(self):
   150                                                   """
   151                                                   Refreshes the state of this instance by re-querying the cloud provider
   152                                                   for its latest state.
   153                                                   """
   154                                                   log.debug("Refreshing OpenStack Machine Image")
   155                                                   image = self._provider.compute.images.get(self.id)
   156                                                   if image:
   157                                                       # pylint:disable=protected-access
   158                                                       self._os_image = image._os_image
   159                                                   else:
   160                                                       # The image no longer exists and cannot be refreshed.
   161                                                       # set the status to unknown
   162                                                       self._os_image.status = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 312

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   312                                               @label.setter
   313                                               # pylint:disable=arguments-differ
   314                                               @profile
   315                                               def label(self, value):
   316                                                   """
   317                                                   Set the instance label.
   318                                                   """
   319                                                   self.assert_valid_resource_label(value)
   320                                           
   321                                                   self._os_instance.name = value
   322                                                   self._os_instance.update(name=value or "cb-inst")

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 493

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   493                                               @profile
   494                                               def refresh(self):
   495                                                   """
   496                                                   Refreshes the state of this instance by re-querying the cloud provider
   497                                                   for its latest state.
   498                                                   """
   499                                                   instance = self._provider.compute.instances.get(
   500                                                       self.id)
   501                                                   if instance:
   502                                                       # pylint:disable=protected-access
   503                                                       self._os_instance = instance._os_instance
   504                                                   else:
   505                                                       # The instance no longer exists and cannot be refreshed.
   506                                                       # set the status to unknown
   507                                                       self._os_instance.status = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 582

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   582                                               @label.setter
   583                                               # pylint:disable=arguments-differ
   584                                               @profile
   585                                               def label(self, value):
   586                                                   """
   587                                                   Set the volume label.
   588                                                   """
   589                                                   self.assert_valid_resource_label(value)
   590                                                   self._volume.name = value
   591                                                   self._volume.update(name=value or "")

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: description at line 597

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   597                                               @description.setter
   598                                               @profile
   599                                               def description(self, value):
   600                                                   self._volume.description = value
   601                                                   self._volume.update(description=value)

Total time: 0.726248 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 662

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   662                                               @profile
   663                                               def refresh(self):
   664                                                   """
   665                                                   Refreshes the state of this volume by re-querying the cloud provider
   666                                                   for its latest state.
   667                                                   """
   668         1         24.0     24.0      0.0          vol = self._provider.storage.volumes.get(
   669         1     726215.0 726215.0    100.0              self.id)
   670         1          2.0      2.0      0.0          if vol:
   671                                                       # pylint:disable=protected-access
   672         1          7.0      7.0      0.0              self._volume = vol._volume  # pylint:disable=protected-access
   673                                                   else:
   674                                                       # The volume no longer exists and cannot be refreshed.
   675                                                       # set the status to unknown
   676                                                       self._volume.status = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 710

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   710                                               @label.setter
   711                                               # pylint:disable=arguments-differ
   712                                               @profile
   713                                               def label(self, value):
   714                                                   """
   715                                                   Set the snapshot label.
   716                                                   """
   717                                                   self.assert_valid_resource_label(value)
   718                                                   self._snapshot.name = value
   719                                                   self._snapshot.update(name=value or "")

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: description at line 725

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   725                                               @description.setter
   726                                               @profile
   727                                               def description(self, value):
   728                                                   self._snapshot.description = value
   729                                                   self._snapshot.update(description=value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 748

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   748                                               @profile
   749                                               def refresh(self):
   750                                                   """
   751                                                   Refreshes the state of this snapshot by re-querying the cloud provider
   752                                                   for its latest state.
   753                                                   """
   754                                                   snap = self._provider.storage.snapshots.get(
   755                                                       self.id)
   756                                                   if snap:
   757                                                       # pylint:disable=protected-access
   758                                                       self._snapshot = snap._snapshot
   759                                                   else:
   760                                                       # The snapshot no longer exists and cannot be refreshed.
   761                                                       # set the status to unknown
   762                                                       self._snapshot.status = 'unknown'

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 811

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   811                                               @label.setter
   812                                               @profile
   813                                               def label(self, value):
   814                                                   """
   815                                                   Set the network label.
   816                                                   """
   817                                                   self.assert_valid_resource_label(value)
   818                                                   self._provider.neutron.update_network(
   819                                                       self.id, {'network': {'name': value or ""}})
   820                                                   self.refresh()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @profile
   843                                               def refresh(self):
   844                                                   """Refresh the state of this network by re-querying the provider."""
   845                                                   network = self._provider.networking.networks.get(self.id)
   846                                                   if network:
   847                                                       # pylint:disable=protected-access
   848                                                       self._network = network._network
   849                                                   else:
   850                                                       # Network no longer exists
   851                                                       self._network = {}

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 877

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   877                                               @label.setter
   878                                               @profile
   879                                               def label(self, value):  # pylint:disable=arguments-differ
   880                                                   """
   881                                                   Set the subnet label.
   882                                                   """
   883                                                   self.assert_valid_resource_label(value)
   884                                                   self._provider.neutron.update_subnet(
   885                                                       self.id, {'subnet': {'name': value or ""}})
   886                                                   self._subnet['name'] = value

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 910

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   910                                               @profile
   911                                               def refresh(self):
   912                                                   subnet = self._provider.networking.subnets.get(self.id)
   913                                                   if subnet:
   914                                                       # pylint:disable=protected-access
   915                                                       self._subnet = subnet._subnet
   916                                                       self._state = SubnetState.AVAILABLE
   917                                                   else:
   918                                                       # subnet no longer exists
   919                                                       self._state = SubnetState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 944

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   944                                               @profile
   945                                               def refresh(self):
   946                                                   net = self._provider.networking.networks.get(
   947                                                       self._ip.floating_network_id)
   948                                                   gw = net.gateways.get_or_create()
   949                                                   fip = gw.floating_ips.get(self.id)
   950                                                   # pylint:disable=protected-access
   951                                                   self._ip = fip._ip

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 976

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   976                                               @label.setter
   977                                               @profile
   978                                               def label(self, value):  # pylint:disable=arguments-differ
   979                                                   """
   980                                                   Set the router label.
   981                                                   """
   982                                                   self.assert_valid_resource_label(value)
   983                                                   self._router = self._provider.os_conn.update_router(self.id, value)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 985

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   985                                               @profile
   986                                               def refresh(self):
   987                                                   self._router = self._provider.os_conn.get_router(self.id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 1070

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1070                                               @profile
  1071                                               def refresh(self):
  1072                                                   """Refresh the state of this network by re-querying the provider."""
  1073                                                   network = self._provider.networking.networks.get(self.id)
  1074                                                   if network:
  1075                                                       # pylint:disable=protected-access
  1076                                                       self._gateway_net = network._network
  1077                                                   else:
  1078                                                       # subnet no longer exists
  1079                                                       self._gateway_net.state = NetworkState.UNKNOWN

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: description at line 1137

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1137                                               @description.setter
  1138                                               @profile
  1139                                               def description(self, value):
  1140                                                   if not value:
  1141                                                       value = ""
  1142                                                   value += " [{}{}]".format(self._network_id_tag,
  1143                                                                             self.network_id)
  1144                                                   self._provider.os_conn.network.update_security_group(
  1145                                                       self.id, description=value)
  1146                                                   self.refresh()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: label at line 1159

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1159                                               @label.setter
  1160                                               # pylint:disable=arguments-differ
  1161                                               @profile
  1162                                               def label(self, value):
  1163                                                   self.assert_valid_resource_label(value)
  1164                                                   self._provider.os_conn.network.update_security_group(
  1165                                                       self.id, name=value or "")
  1166                                                   self.refresh()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 1172

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1172                                               @profile
  1173                                               def refresh(self):
  1174                                                   self._vm_firewall = self._provider.os_conn.network.get_security_group(
  1175                                                       self.id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/resources.py
Function: refresh at line 1345

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1345                                               @profile
  1346                                               def refresh(self):
  1347                                                   self._obj = self.cbcontainer.objects.get(self.id)._obj

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get_or_create_ec2_credentials at line 101

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   101                                               @profile
   102                                               def get_or_create_ec2_credentials(self):
   103                                                   """
   104                                                   A provider specific method than returns the ec2 credentials for the
   105                                                   current user, or creates a new pair if one doesn't exist.
   106                                                   """
   107                                                   keystone = self.provider.keystone
   108                                                   if hasattr(keystone, 'ec2'):
   109                                                       user_id = keystone.session.get_user_id()
   110                                                       user_creds = [cred for cred in keystone.ec2.list(user_id) if
   111                                                                     cred.tenant_id == keystone.session.get_project_id()]
   112                                                       if user_creds:
   113                                                           return user_creds[0]
   114                                                       else:
   115                                                           return keystone.ec2.create(
   116                                                               user_id, keystone.session.get_project_id())
   117                                           
   118                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get_ec2_endpoints at line 120

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   120                                               @profile
   121                                               def get_ec2_endpoints(self):
   122                                                   """
   123                                                   A provider specific method than returns the ec2 endpoints if
   124                                                   available.
   125                                                   """
   126                                                   keystone = self.provider.keystone
   127                                                   ec2_url = keystone.session.get_endpoint(service_type='ec2')
   128                                                   s3_url = keystone.session.get_endpoint(service_type='s3')
   129                                           
   130                                                   return {'ec2_endpoint': ec2_url,
   131                                                           's3_endpoint': s3_url}

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
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
   146                                                   log.debug("Returning KeyPair with the id %s", key_pair_id)
   147                                                   try:
   148                                                       return OpenStackKeyPair(
   149                                                           self.provider, self.provider.nova.keypairs.get(key_pair_id))
   150                                                   except NovaNotFound:
   151                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   152                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
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
   164                                                   keypairs = self.provider.nova.keypairs.list()
   165                                                   results = [OpenStackKeyPair(self.provider, kp)
   166                                                              for kp in keypairs]
   167                                                   log.debug("Listing all key pairs associated with OpenStack "
   168                                                             "Account: %s", results)
   169                                                   return ClientPagedResultList(self.provider, results,
   170                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 172

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   172                                               @dispatch(event="provider.security.key_pairs.find",
   173                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   174                                               @profile
   175                                               def find(self, **kwargs):
   176                                                   name = kwargs.pop('name', None)
   177                                           
   178                                                   # All kwargs should have been popped at this time.
   179                                                   if len(kwargs) > 0:
   180                                                       raise InvalidParamException(
   181                                                           "Unrecognised parameters for search: %s. Supported "
   182                                                           "attributes: %s" % (kwargs, 'name'))
   183                                           
   184                                                   keypairs = self.provider.nova.keypairs.findall(name=name)
   185                                                   results = [OpenStackKeyPair(self.provider, kp)
   186                                                              for kp in keypairs]
   187                                                   log.debug("Searching for %s in: %s", name, keypairs)
   188                                                   return ClientPagedResultList(self.provider, results)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 190

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   190                                               @dispatch(event="provider.security.key_pairs.create",
   191                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   192                                               @profile
   193                                               def create(self, name, public_key_material=None):
   194                                                   OpenStackKeyPair.assert_valid_resource_name(name)
   195                                                   existing_kp = self.find(name=name)
   196                                                   if existing_kp:
   197                                                       raise DuplicateResourceException(
   198                                                           'Keypair already exists with name {0}'.format(name))
   199                                           
   200                                                   private_key = None
   201                                                   if not public_key_material:
   202                                                       public_key_material, private_key = cb_helpers.generate_key_pair()
   203                                           
   204                                                   kp = self.provider.nova.keypairs.create(name,
   205                                                                                           public_key=public_key_material)
   206                                                   cb_kp = OpenStackKeyPair(self.provider, kp)
   207                                                   cb_kp.material = private_key
   208                                                   return cb_kp

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 210

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   210                                               @dispatch(event="provider.security.key_pairs.delete",
   211                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   212                                               @profile
   213                                               def delete(self, key_pair):
   214                                                   keypair = (key_pair if isinstance(key_pair, OpenStackKeyPair)
   215                                                              else self.get(key_pair))
   216                                                   if keypair:
   217                                                       # pylint:disable=protected-access
   218                                                       keypair._key_pair.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 226

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   226                                               @dispatch(event="provider.security.vm_firewalls.get",
   227                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   228                                               @profile
   229                                               def get(self, vm_firewall_id):
   230                                                   try:
   231                                                       return OpenStackVMFirewall(
   232                                                           self.provider,
   233                                                           self.provider.os_conn.network
   234                                                               .get_security_group(vm_firewall_id))
   235                                                   except (ResourceNotFound, NotFoundException):
   236                                                       log.debug("Firewall %s not found.", vm_firewall_id)
   237                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 239

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   239                                               @dispatch(event="provider.security.vm_firewalls.list",
   240                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   241                                               @profile
   242                                               def list(self, limit=None, marker=None):
   243                                                   firewalls = [
   244                                                       OpenStackVMFirewall(self.provider, fw)
   245                                                       for fw in self.provider.os_conn.network.security_groups()]
   246                                           
   247                                                   return ClientPagedResultList(self.provider, firewalls,
   248                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 250

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   250                                               @cb_helpers.deprecated_alias(network_id='network')
   251                                               @dispatch(event="provider.security.vm_firewalls.create",
   252                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   253                                               @profile
   254                                               def create(self, label, network, description=None):
   255                                                   OpenStackVMFirewall.assert_valid_resource_label(label)
   256                                                   net_id = network.id if isinstance(network, Network) else network
   257                                                   # We generally simulate a network being associated with a firewall
   258                                                   # by storing the supplied value in the firewall description field that
   259                                                   # is not modifiable after creation; however, because of some networking
   260                                                   # specificity in Nectar, we must also allow an empty network id value.
   261                                                   if not net_id:
   262                                                       net_id = ""
   263                                                   if not description:
   264                                                       description = ""
   265                                                   description += " [{}{}]".format(OpenStackVMFirewall._network_id_tag,
   266                                                                                   net_id)
   267                                                   sg = self.provider.os_conn.network.create_security_group(
   268                                                       name=label, description=description)
   269                                                   if sg:
   270                                                       return OpenStackVMFirewall(self.provider, sg)
   271                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   273                                               @dispatch(event="provider.security.vm_firewalls.delete",
   274                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   275                                               @profile
   276                                               def delete(self, vm_firewall):
   277                                                   fw = (vm_firewall if isinstance(vm_firewall, OpenStackVMFirewall)
   278                                                         else self.get(vm_firewall))
   279                                                   if fw:
   280                                                       # pylint:disable=protected-access
   281                                                       fw._vm_firewall.delete(self.provider.os_conn.session)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 289

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   289                                               @dispatch(event="provider.security.vm_firewall_rules.list",
   290                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   291                                               @profile
   292                                               def list(self, firewall, limit=None, marker=None):
   293                                                   # pylint:disable=protected-access
   294                                                   rules = [OpenStackVMFirewallRule(firewall, r)
   295                                                            for r in firewall._vm_firewall.security_group_rules]
   296                                                   return ClientPagedResultList(self.provider, rules,
   297                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 299

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   299                                               @dispatch(event="provider.security.vm_firewall_rules.create",
   300                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   301                                               @profile
   302                                               def create(self, firewall, direction, protocol=None, from_port=None,
   303                                                          to_port=None, cidr=None, src_dest_fw=None):
   304                                                   src_dest_fw_id = (src_dest_fw.id if isinstance(src_dest_fw,
   305                                                                                                  OpenStackVMFirewall)
   306                                                                     else src_dest_fw)
   307                                           
   308                                                   try:
   309                                                       if direction == TrafficDirection.INBOUND:
   310                                                           os_direction = 'ingress'
   311                                                       elif direction == TrafficDirection.OUTBOUND:
   312                                                           os_direction = 'egress'
   313                                                       else:
   314                                                           raise InvalidValueException("direction", direction)
   315                                                       # pylint:disable=protected-access
   316                                                       rule = self.provider.os_conn.network.create_security_group_rule(
   317                                                           security_group_id=firewall.id,
   318                                                           direction=os_direction,
   319                                                           port_range_max=to_port,
   320                                                           port_range_min=from_port,
   321                                                           protocol=protocol,
   322                                                           remote_ip_prefix=cidr,
   323                                                           remote_group_id=src_dest_fw_id)
   324                                                       firewall.refresh()
   325                                                       return OpenStackVMFirewallRule(firewall, rule.to_dict())
   326                                                   except HttpException as e:
   327                                                       firewall.refresh()
   328                                                       # 409=Conflict, raised for duplicate rule
   329                                                       if e.status_code == 409:
   330                                                           existing = self.find(firewall, direction=direction,
   331                                                                                protocol=protocol, from_port=from_port,
   332                                                                                to_port=to_port, cidr=cidr,
   333                                                                                src_dest_fw_id=src_dest_fw_id)
   334                                                           return existing[0]
   335                                                       else:
   336                                                           raise e

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 338

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   338                                               @dispatch(event="provider.security.vm_firewall_rules.delete",
   339                                                         priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
   340                                               @profile
   341                                               def delete(self, firewall, rule):
   342                                                   rule_id = (rule.id if isinstance(rule, OpenStackVMFirewallRule)
   343                                                              else rule)
   344                                                   self.provider.os_conn.network.delete_security_group_rule(rule_id)
   345                                                   firewall.refresh()

Total time: 0.683317 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   381                                               @dispatch(event="provider.storage.volumes.get",
   382                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   383                                               @profile
   384                                               def get(self, volume_id):
   385         1          1.0      1.0      0.0          try:
   386         1          0.0      0.0      0.0              return OpenStackVolume(
   387         1     683316.0 683316.0    100.0                  self.provider, self.provider.cinder.volumes.get(volume_id))
   388                                                   except CinderNotFound:
   389                                                       log.debug("Volume %s was not found.", volume_id)
   390                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 392

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   392                                               @dispatch(event="provider.storage.volumes.find",
   393                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   394                                               @profile
   395                                               def find(self, **kwargs):
   396                                                   label = kwargs.pop('label', None)
   397                                           
   398                                                   # All kwargs should have been popped at this time.
   399                                                   if len(kwargs) > 0:
   400                                                       raise InvalidParamException(
   401                                                           "Unrecognised parameters for search: %s. Supported "
   402                                                           "attributes: %s" % (kwargs, 'label'))
   403                                           
   404                                                   log.debug("Searching for an OpenStack Volume with the label %s", label)
   405                                                   search_opts = {'name': label}
   406                                                   cb_vols = [
   407                                                       OpenStackVolume(self.provider, vol)
   408                                                       for vol in self.provider.cinder.volumes.list(
   409                                                           search_opts=search_opts,
   410                                                           limit=oshelpers.os_result_limit(self.provider),
   411                                                           marker=None)]
   412                                           
   413                                                   return oshelpers.to_server_paged_list(self.provider, cb_vols)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 415

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   415                                               @dispatch(event="provider.storage.volumes.list",
   416                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   417                                               @profile
   418                                               def list(self, limit=None, marker=None):
   419                                                   cb_vols = [
   420                                                       OpenStackVolume(self.provider, vol)
   421                                                       for vol in self.provider.cinder.volumes.list(
   422                                                           limit=oshelpers.os_result_limit(self.provider, limit),
   423                                                           marker=marker)]
   424                                           
   425                                                   return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

Total time: 2.18261 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 427

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   427                                               @dispatch(event="provider.storage.volumes.create",
   428                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   429                                               @profile
   430                                               def create(self, label, size, zone, snapshot=None, description=None):
   431         1         12.0     12.0      0.0          OpenStackVolume.assert_valid_resource_label(label)
   432         1          2.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   433         1          1.0      1.0      0.0          snapshot_id = snapshot.id if isinstance(
   434         1          1.0      1.0      0.0              snapshot, OpenStackSnapshot) and snapshot else snapshot
   435                                           
   436         1     884819.0 884819.0     40.5          os_vol = self.provider.cinder.volumes.create(
   437         1          1.0      1.0      0.0              size, name=label, description=description,
   438         1    1297753.0 1297753.0     59.5              availability_zone=zone_id, snapshot_id=snapshot_id)
   439         1         21.0     21.0      0.0          return OpenStackVolume(self.provider, os_vol)

Total time: 0.582492 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 441

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   441                                               @dispatch(event="provider.storage.volumes.delete",
   442                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   443                                               @profile
   444                                               def delete(self, volume):
   445         1          2.0      2.0      0.0          volume = (volume if isinstance(volume, OpenStackVolume)
   446                                                             else self.get(volume))
   447         1          1.0      1.0      0.0          if volume:
   448                                                       # pylint:disable=protected-access
   449         1     582489.0 582489.0    100.0              volume._volume.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 457

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   457                                               @dispatch(event="provider.storage.snapshots.get",
   458                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   459                                               @profile
   460                                               def get(self, snapshot_id):
   461                                                   try:
   462                                                       return OpenStackSnapshot(
   463                                                           self.provider,
   464                                                           self.provider.cinder.volume_snapshots.get(snapshot_id))
   465                                                   except CinderNotFound:
   466                                                       log.debug("Snapshot %s was not found.", snapshot_id)
   467                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 469

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   469                                               @dispatch(event="provider.storage.snapshots.find",
   470                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   471                                               @profile
   472                                               def find(self, **kwargs):
   473                                                   label = kwargs.pop('label', None)
   474                                           
   475                                                   # All kwargs should have been popped at this time.
   476                                                   if len(kwargs) > 0:
   477                                                       raise InvalidParamException(
   478                                                           "Unrecognised parameters for search: %s. Supported "
   479                                                           "attributes: %s" % (kwargs, 'label'))
   480                                           
   481                                                   search_opts = {'name': label,  # TODO: Cinder is ignoring name
   482                                                                  'limit': oshelpers.os_result_limit(self.provider),
   483                                                                  'marker': None}
   484                                                   log.debug("Searching for an OpenStack snapshot with the following "
   485                                                             "params: %s", search_opts)
   486                                                   cb_snaps = [
   487                                                       OpenStackSnapshot(self.provider, snap) for
   488                                                       snap in self.provider.cinder.volume_snapshots.list(search_opts)
   489                                                       if snap.name == label]
   490                                           
   491                                                   return oshelpers.to_server_paged_list(self.provider, cb_snaps)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 493

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   493                                               @dispatch(event="provider.storage.snapshots.list",
   494                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   495                                               @profile
   496                                               def list(self, limit=None, marker=None):
   497                                                   cb_snaps = [
   498                                                       OpenStackSnapshot(self.provider, snap) for
   499                                                       snap in self.provider.cinder.volume_snapshots.list(
   500                                                           search_opts={'limit': oshelpers.os_result_limit(self.provider,
   501                                                                                                           limit),
   502                                                                        'marker': marker})]
   503                                                   return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 505

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   505                                               @dispatch(event="provider.storage.snapshots.create",
   506                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   507                                               @profile
   508                                               def create(self, label, volume, description=None):
   509                                                   OpenStackSnapshot.assert_valid_resource_label(label)
   510                                                   volume_id = (volume.id if isinstance(volume, OpenStackVolume)
   511                                                                else volume)
   512                                           
   513                                                   os_snap = self.provider.cinder.volume_snapshots.create(
   514                                                       volume_id, name=label,
   515                                                       description=description)
   516                                                   return OpenStackSnapshot(self.provider, os_snap)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 518

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   518                                               @dispatch(event="provider.storage.snapshots.delete",
   519                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   520                                               @profile
   521                                               def delete(self, snapshot):
   522                                                   s = (snapshot if isinstance(snapshot, OpenStackSnapshot) else
   523                                                        self.get(snapshot))
   524                                                   if s:
   525                                                       # pylint:disable=protected-access
   526                                                       s._snapshot.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 534

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   534                                               @dispatch(event="provider.storage.buckets.get",
   535                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   536                                               @profile
   537                                               def get(self, bucket_id):
   538                                                   """
   539                                                   Returns a bucket given its ID. Returns ``None`` if the bucket
   540                                                   does not exist.
   541                                                   """
   542                                                   _, container_list = self.provider.swift.get_account(
   543                                                       prefix=bucket_id)
   544                                                   if container_list:
   545                                                       return OpenStackBucket(self.provider,
   546                                                                              next((c for c in container_list
   547                                                                                    if c['name'] == bucket_id), None))
   548                                                   else:
   549                                                       log.debug("Bucket %s was not found.", bucket_id)
   550                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 552

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   552                                               @dispatch(event="provider.storage.buckets.find",
   553                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   554                                               @profile
   555                                               def find(self, **kwargs):
   556                                                   name = kwargs.pop('name', None)
   557                                           
   558                                                   # All kwargs should have been popped at this time.
   559                                                   if len(kwargs) > 0:
   560                                                       raise InvalidParamException(
   561                                                           "Unrecognised parameters for search: %s. Supported "
   562                                                           "attributes: %s" % (kwargs, 'name'))
   563                                                   _, container_list = self.provider.swift.get_account()
   564                                                   cb_buckets = [OpenStackBucket(self.provider, c)
   565                                                                 for c in container_list
   566                                                                 if name in c.get("name")]
   567                                                   return oshelpers.to_server_paged_list(self.provider, cb_buckets)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 569

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   569                                               @dispatch(event="provider.storage.buckets.list",
   570                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   571                                               @profile
   572                                               def list(self, limit=None, marker=None):
   573                                                   _, container_list = self.provider.swift.get_account(
   574                                                       limit=oshelpers.os_result_limit(self.provider, limit),
   575                                                       marker=marker)
   576                                                   cb_buckets = [OpenStackBucket(self.provider, c)
   577                                                                 for c in container_list]
   578                                                   return oshelpers.to_server_paged_list(self.provider, cb_buckets, limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 580

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   580                                               @dispatch(event="provider.storage.buckets.create",
   581                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   582                                               @profile
   583                                               def create(self, name, location=None):
   584                                                   OpenStackBucket.assert_valid_resource_name(name)
   585                                                   location = location or self.provider.region_name
   586                                                   try:
   587                                                       self.provider.swift.head_container(name)
   588                                                       raise DuplicateResourceException(
   589                                                           'Bucket already exists with name {0}'.format(name))
   590                                                   except SwiftClientException:
   591                                                       self.provider.swift.put_container(name)
   592                                                       return self.get(name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 594

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   594                                               @dispatch(event="provider.storage.buckets.delete",
   595                                                         priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
   596                                               @profile
   597                                               def delete(self, bucket):
   598                                                   b_id = bucket.id if isinstance(bucket, OpenStackBucket) else bucket
   599                                                   self.provider.swift.delete_container(b_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 607

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   607                                               @profile
   608                                               def get(self, bucket, name):
   609                                                   """
   610                                                   Retrieve a given object from this bucket.
   611                                                   """
   612                                                   # Swift always returns a reference for the container first,
   613                                                   # followed by a list containing references to objects.
   614                                                   _, object_list = self.provider.swift.get_container(
   615                                                       bucket.name, prefix=name)
   616                                                   # Loop through list of objects looking for an exact name vs. a prefix
   617                                                   for obj in object_list:
   618                                                       if obj.get('name') == name:
   619                                                           return OpenStackBucketObject(self.provider,
   620                                                                                        bucket,
   621                                                                                        obj)
   622                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 624

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   624                                               @profile
   625                                               def list(self, bucket, limit=None, marker=None, prefix=None):
   626                                                   """
   627                                                   List all objects within this bucket.
   628                                           
   629                                                   :rtype: BucketObject
   630                                                   :return: List of all available BucketObjects within this bucket.
   631                                                   """
   632                                                   _, object_list = self.provider.swift.get_container(
   633                                                       bucket.name,
   634                                                       limit=oshelpers.os_result_limit(self.provider, limit),
   635                                                       marker=marker, prefix=prefix)
   636                                                   cb_objects = [OpenStackBucketObject(
   637                                                       self.provider, bucket, obj) for obj in object_list]
   638                                           
   639                                                   return oshelpers.to_server_paged_list(
   640                                                       self.provider,
   641                                                       cb_objects,
   642                                                       limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 644

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   644                                               @profile
   645                                               def find(self, bucket, **kwargs):
   646                                                   _, obj_list = self.provider.swift.get_container(bucket.name)
   647                                                   cb_objs = [OpenStackBucketObject(self.provider, bucket, obj)
   648                                                              for obj in obj_list]
   649                                                   filters = ['name']
   650                                                   matches = cb_helpers.generic_find(filters, kwargs, cb_objs)
   651                                                   return ClientPagedResultList(self.provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 653

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   653                                               @profile
   654                                               def create(self, bucket, object_name):
   655                                                   self.provider.swift.put_object(bucket.name, object_name, None)
   656                                                   return self.get(bucket, object_name)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 690

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   690                                               @profile
   691                                               def get(self, image_id):
   692                                                   """
   693                                                   Returns an Image given its id
   694                                                   """
   695                                                   log.debug("Getting OpenStack Image with the id: %s", image_id)
   696                                                   try:
   697                                                       return OpenStackMachineImage(
   698                                                           self.provider, self.provider.os_conn.image.get_image(image_id))
   699                                                   except (NotFoundException, ResourceNotFound):
   700                                                       log.debug("Image %s not found", image_id)
   701                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 703

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   703                                               @profile
   704                                               def find(self, **kwargs):
   705                                                   filters = ['label']
   706                                                   obj_list = self
   707                                                   return cb_helpers.generic_find(filters, kwargs, obj_list)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 709

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   709                                               @profile
   710                                               def list(self, filter_by_owner=True, limit=None, marker=None):
   711                                                   """
   712                                                   List all images.
   713                                                   """
   714                                                   project_id = None
   715                                                   if filter_by_owner:
   716                                                       project_id = self.provider.os_conn.session.get_project_id()
   717                                                   os_images = self.provider.os_conn.image.images(
   718                                                       owner=project_id,
   719                                                       limit=oshelpers.os_result_limit(self.provider, limit),
   720                                                       marker=marker)
   721                                           
   722                                                   cb_images = [
   723                                                       OpenStackMachineImage(self.provider, img)
   724                                                       for img in os_images]
   725                                                   return oshelpers.to_server_paged_list(self.provider, cb_images, limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create_launch_config at line 783

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   783                                               @profile
   784                                               def create_launch_config(self):
   785                                                   return BaseLaunchConfig(self.provider)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 787

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   787                                               @dispatch(event="provider.compute.instances.create",
   788                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   789                                               @profile
   790                                               def create(self, label, image, vm_type, subnet, zone,
   791                                                          key_pair=None, vm_firewalls=None, user_data=None,
   792                                                          launch_config=None, **kwargs):
   793                                                   OpenStackInstance.assert_valid_resource_label(label)
   794                                                   image_id = image.id if isinstance(image, MachineImage) else image
   795                                                   vm_size = vm_type.id if \
   796                                                       isinstance(vm_type, VMType) else \
   797                                                       self.provider.compute.vm_types.find(
   798                                                           name=vm_type)[0].id
   799                                                   if isinstance(subnet, Subnet):
   800                                                       subnet_id = subnet.id
   801                                                       net_id = subnet.network_id
   802                                                   else:
   803                                                       subnet_id = subnet
   804                                                       net_id = (self.provider.networking.subnets
   805                                                                 .get(subnet_id).network_id
   806                                                                 if subnet_id else None)
   807                                                   zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   808                                                   key_pair_name = key_pair.name if \
   809                                                       isinstance(key_pair, KeyPair) else key_pair
   810                                                   bdm = None
   811                                                   if launch_config:
   812                                                       bdm = self._to_block_device_mapping(launch_config)
   813                                           
   814                                                   # Security groups must be passed in as a list of IDs and attached to a
   815                                                   # port if a port is being created. Otherwise, the security groups must
   816                                                   # be passed in as a list of names to the servers.create() call.
   817                                                   # OpenStack will respect the port's security groups first and then
   818                                                   # fall-back to the named security groups.
   819                                                   sg_name_list = []
   820                                                   nics = None
   821                                                   if subnet_id:
   822                                                       log.debug("Creating network port for %s in subnet: %s",
   823                                                                 label, subnet_id)
   824                                                       sg_list = []
   825                                                       if vm_firewalls:
   826                                                           if isinstance(vm_firewalls, list) and \
   827                                                                   isinstance(vm_firewalls[0], VMFirewall):
   828                                                               sg_list = vm_firewalls
   829                                                           else:
   830                                                               sg_list = (self.provider.security.vm_firewalls
   831                                                                          .find(label=sg) for sg in vm_firewalls)
   832                                                               sg_list = (sg[0] for sg in sg_list if sg)
   833                                                       sg_id_list = [sg.id for sg in sg_list]
   834                                                       port_def = {
   835                                                           "port": {
   836                                                               "admin_state_up": True,
   837                                                               "name": OpenStackInstance._generate_name_from_label(
   838                                                                   label, 'cb-port'),
   839                                                               "network_id": net_id,
   840                                                               "fixed_ips": [{"subnet_id": subnet_id}],
   841                                                               "security_groups": sg_id_list
   842                                                           }
   843                                                       }
   844                                                       port_id = self.provider.neutron.create_port(port_def)['port']['id']
   845                                                       nics = [{'net-id': net_id, 'port-id': port_id}]
   846                                                   else:
   847                                                       if vm_firewalls:
   848                                                           if isinstance(vm_firewalls, list) and \
   849                                                                   isinstance(vm_firewalls[0], VMFirewall):
   850                                                               sg_name_list = [sg.name for sg in vm_firewalls]
   851                                                           else:
   852                                                               sg_list = (self.provider.security.vm_firewalls.get(sg)
   853                                                                          for sg in vm_firewalls)
   854                                                               sg_name_list = (sg[0].name for sg in sg_list if sg)
   855                                           
   856                                                   log.debug("Launching in subnet %s", subnet_id)
   857                                                   os_instance = self.provider.nova.servers.create(
   858                                                       label,
   859                                                       None if self._has_root_device(launch_config) else image_id,
   860                                                       vm_size,
   861                                                       min_count=1,
   862                                                       max_count=1,
   863                                                       availability_zone=zone_id,
   864                                                       key_name=key_pair_name,
   865                                                       security_groups=sg_name_list,
   866                                                       userdata=str(user_data) or None,
   867                                                       block_device_mapping_v2=bdm,
   868                                                       nics=nics)
   869                                                   return OpenStackInstance(self.provider, os_instance)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 871

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   871                                               @dispatch(event="provider.compute.instances.find",
   872                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   873                                               @profile
   874                                               def find(self, **kwargs):
   875                                                   label = kwargs.pop('label', None)
   876                                           
   877                                                   # All kwargs should have been popped at this time.
   878                                                   if len(kwargs) > 0:
   879                                                       raise InvalidParamException(
   880                                                           "Unrecognised parameters for search: %s. Supported "
   881                                                           "attributes: %s" % (kwargs, 'label'))
   882                                           
   883                                                   search_opts = {'name': label}
   884                                                   cb_insts = [
   885                                                       OpenStackInstance(self.provider, inst)
   886                                                       for inst in self.provider.nova.servers.list(
   887                                                           search_opts=search_opts,
   888                                                           limit=oshelpers.os_result_limit(self.provider),
   889                                                           marker=None)]
   890                                                   return oshelpers.to_server_paged_list(self.provider, cb_insts)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 892

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   892                                               @dispatch(event="provider.compute.instances.list",
   893                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   894                                               @profile
   895                                               def list(self, limit=None, marker=None):
   896                                                   """
   897                                                   List all instances.
   898                                                   """
   899                                                   cb_insts = [
   900                                                       OpenStackInstance(self.provider, inst)
   901                                                       for inst in self.provider.nova.servers.list(
   902                                                           limit=oshelpers.os_result_limit(self.provider, limit),
   903                                                           marker=marker)]
   904                                                   return oshelpers.to_server_paged_list(self.provider, cb_insts, limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 906

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   906                                               @dispatch(event="provider.compute.instances.get",
   907                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   908                                               @profile
   909                                               def get(self, instance_id):
   910                                                   """
   911                                                   Returns an instance given its id.
   912                                                   """
   913                                                   try:
   914                                                       os_instance = self.provider.nova.servers.get(instance_id)
   915                                                       return OpenStackInstance(self.provider, os_instance)
   916                                                   except NovaNotFound:
   917                                                       log.debug("Instance %s was not found.", instance_id)
   918                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 920

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   920                                               @dispatch(event="provider.compute.instances.delete",
   921                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   922                                               @profile
   923                                               def delete(self, instance):
   924                                                   ins = (instance if isinstance(instance, OpenStackInstance) else
   925                                                          self.get(instance))
   926                                                   if ins:
   927                                                       # pylint:disable=protected-access
   928                                                       os_instance = ins._os_instance
   929                                                       # delete the port we created when launching
   930                                                       # Assumption: it's the first interface in the list
   931                                                       iface_list = os_instance.interface_list()
   932                                                       if iface_list:
   933                                                           self.provider.neutron.delete_port(iface_list[0].port_id)
   934                                                       os_instance.delete()

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 942

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   942                                               @dispatch(event="provider.compute.vm_types.list",
   943                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   944                                               @profile
   945                                               def list(self, limit=None, marker=None):
   946                                                   cb_itypes = [
   947                                                       OpenStackVMType(self.provider, obj)
   948                                                       for obj in self.provider.nova.flavors.list(
   949                                                           limit=oshelpers.os_result_limit(self.provider, limit),
   950                                                           marker=marker)]
   951                                           
   952                                                   return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 960

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   960                                               @dispatch(event="provider.compute.regions.get",
   961                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   962                                               @profile
   963                                               def get(self, region_id):
   964                                                   log.debug("Getting OpenStack Region with the id: %s", region_id)
   965                                                   region = (r for r in self if r.id == region_id)
   966                                                   return next(region, None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 968

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   968                                               @dispatch(event="provider.compute.regions.list",
   969                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   970                                               @profile
   971                                               def list(self, limit=None, marker=None):
   972                                                   # pylint:disable=protected-access
   973                                                   if self.provider._keystone_version == 3:
   974                                                       os_regions = [OpenStackRegion(self.provider, region)
   975                                                                     for region in self.provider.keystone.regions.list()]
   976                                                       return ClientPagedResultList(self.provider, os_regions,
   977                                                                                    limit=limit, marker=marker)
   978                                                   else:
   979                                                       # Keystone v3 onwards supports directly listing regions
   980                                                       # but for v2, this convoluted method is necessary.
   981                                                       regions = (
   982                                                           endpoint.get('region') or endpoint.get('region_id')
   983                                                           for svc in self.provider.keystone.service_catalog.get_data()
   984                                                           for endpoint in svc.get('endpoints', [])
   985                                                       )
   986                                                       regions = set(region for region in regions if region)
   987                                                       os_regions = [OpenStackRegion(self.provider, region)
   988                                                                     for region in regions]
   989                                           
   990                                                       return ClientPagedResultList(self.provider, os_regions,
   991                                                                                    limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 1035

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1035                                               @dispatch(event="provider.networking.networks.get",
  1036                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1037                                               @profile
  1038                                               def get(self, network_id):
  1039                                                   network = (n for n in self if n.id == network_id)
  1040                                                   return next(network, None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 1042

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1042                                               @dispatch(event="provider.networking.networks.list",
  1043                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1044                                               @profile
  1045                                               def list(self, limit=None, marker=None):
  1046                                                   networks = [OpenStackNetwork(self.provider, network)
  1047                                                               for network in self.provider.neutron.list_networks()
  1048                                                               .get('networks') if network]
  1049                                                   return ClientPagedResultList(self.provider, networks,
  1050                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 1052

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1052                                               @dispatch(event="provider.networking.networks.find",
  1053                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1054                                               @profile
  1055                                               def find(self, **kwargs):
  1056                                                   label = kwargs.pop('label', None)
  1057                                           
  1058                                                   # All kwargs should have been popped at this time.
  1059                                                   if len(kwargs) > 0:
  1060                                                       raise InvalidParamException(
  1061                                                           "Unrecognised parameters for search: %s. Supported "
  1062                                                           "attributes: %s" % (kwargs, 'label'))
  1063                                           
  1064                                                   log.debug("Searching for OpenStack Network with label: %s", label)
  1065                                                   networks = [OpenStackNetwork(self.provider, network)
  1066                                                               for network in self.provider.neutron.list_networks(
  1067                                                                   name=label)
  1068                                                               .get('networks') if network]
  1069                                                   return ClientPagedResultList(self.provider, networks)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 1071

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1071                                               @dispatch(event="provider.networking.networks.create",
  1072                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1073                                               @profile
  1074                                               def create(self, label, cidr_block):
  1075                                                   OpenStackNetwork.assert_valid_resource_label(label)
  1076                                                   net_info = {'name': label or ""}
  1077                                                   network = self.provider.neutron.create_network({'network': net_info})
  1078                                                   cb_net = OpenStackNetwork(self.provider, network.get('network'))
  1079                                                   if label:
  1080                                                       cb_net.label = label
  1081                                                   return cb_net

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 1083

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1083                                               @dispatch(event="provider.networking.networks.delete",
  1084                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1085                                               @profile
  1086                                               def delete(self, network):
  1087                                                   network = (network if isinstance(network, OpenStackNetwork) else
  1088                                                              self.get(network))
  1089                                                   if not network:
  1090                                                       return
  1091                                                   if not network.external and network.id in str(
  1092                                                           self.provider.neutron.list_networks()):
  1093                                                       # If there are ports associated with the network, it won't delete
  1094                                                       ports = self.provider.neutron.list_ports(
  1095                                                           network_id=network.id).get('ports', [])
  1096                                                       for port in ports:
  1097                                                           try:
  1098                                                               self.provider.neutron.delete_port(port.get('id'))
  1099                                                           except PortNotFoundClient:
  1100                                                               # Ports could have already been deleted if instances
  1101                                                               # are terminated etc. so exceptions can be safely ignored
  1102                                                               pass
  1103                                                       self.provider.neutron.delete_network(network.id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 1111

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1111                                               @dispatch(event="provider.networking.subnets.get",
  1112                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1113                                               @profile
  1114                                               def get(self, subnet_id):
  1115                                                   subnet = (s for s in self if s.id == subnet_id)
  1116                                                   return next(subnet, None)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122                                                   if network:
  1123                                                       network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125                                                       subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128                                                       subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129                                                                  self.provider.neutron.list_subnets().get('subnets', [])]
  1130                                                   return ClientPagedResultList(self.provider, subnets,
  1131                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 1133

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1133                                               @dispatch(event="provider.networking.subnets.create",
  1134                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1135                                               @profile
  1136                                               def create(self, label, network, cidr_block, zone):
  1137                                                   """zone param is ignored."""
  1138                                                   OpenStackSubnet.assert_valid_resource_label(label)
  1139                                                   network_id = (network.id if isinstance(network, OpenStackNetwork)
  1140                                                                 else network)
  1141                                                   subnet_info = {'name': label, 'network_id': network_id,
  1142                                                                  'cidr': cidr_block, 'ip_version': 4}
  1143                                                   subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
  1144                                                             .get('subnet'))
  1145                                                   cb_subnet = OpenStackSubnet(self.provider, subnet)
  1146                                                   return cb_subnet

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 1148

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1148                                               @dispatch(event="provider.networking.subnets.delete",
  1149                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1150                                               @profile
  1151                                               def delete(self, subnet):
  1152                                                   sn_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
  1153                                                   self.provider.neutron.delete_subnet(sn_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160                                                   try:
  1161                                                       sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162                                                       if sn:
  1163                                                           return sn[0]
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

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 1185

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1185                                               @dispatch(event="provider.networking.routers.get",
  1186                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1187                                               @profile
  1188                                               def get(self, router_id):
  1189                                                   log.debug("Getting OpenStack Router with the id: %s", router_id)
  1190                                                   router = self.provider.os_conn.get_router(router_id)
  1191                                                   return OpenStackRouter(self.provider, router) if router else None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 1193

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1193                                               @dispatch(event="provider.networking.routers.list",
  1194                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1195                                               @profile
  1196                                               def list(self, limit=None, marker=None):
  1197                                                   routers = self.provider.os_conn.list_routers()
  1198                                                   os_routers = [OpenStackRouter(self.provider, r) for r in routers]
  1199                                                   return ClientPagedResultList(self.provider, os_routers, limit=limit,
  1200                                                                                marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: find at line 1202

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1202                                               @dispatch(event="provider.networking.routers.find",
  1203                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1204                                               @profile
  1205                                               def find(self, **kwargs):
  1206                                                   obj_list = self
  1207                                                   filters = ['label']
  1208                                                   matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1209                                                   return ClientPagedResultList(self._provider, list(matches))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 1211

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1211                                               @dispatch(event="provider.networking.routers.create",
  1212                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1213                                               @profile
  1214                                               def create(self, label, network):
  1215                                                   """Parameter ``network`` is not used by OpenStack."""
  1216                                                   router = self.provider.os_conn.create_router(name=label)
  1217                                                   return OpenStackRouter(self.provider, router)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 1219

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1219                                               @dispatch(event="provider.networking.routers.delete",
  1220                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1221                                               @profile
  1222                                               def delete(self, router):
  1223                                                   r_id = router.id if isinstance(router, OpenStackRouter) else router
  1224                                                   self.provider.os_conn.delete_router(r_id)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get_or_create at line 1249

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1249                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1250                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1251                                               @profile
  1252                                               def get_or_create(self, network):
  1253                                                   """For OS, inet gtw is any net that has `external` property set."""
  1254                                                   external_nets = (n for n in self._provider.networking.networks
  1255                                                                    if n.external)
  1256                                                   for net in external_nets:
  1257                                                       if self._check_fip_connectivity(network, net):
  1258                                                           return OpenStackInternetGateway(self._provider, net)
  1259                                                   return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 1261

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1261                                               @dispatch(event="provider.networking.gateways.delete",
  1262                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1263                                               @profile
  1264                                               def delete(self, network, gateway):
  1265                                                   pass

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 1267

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1267                                               @dispatch(event="provider.networking.gateways.list",
  1268                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1269                                               @profile
  1270                                               def list(self, network, limit=None, marker=None):
  1271                                                   log.debug("OpenStack listing of all current internet gateways")
  1272                                                   igl = [OpenStackInternetGateway(self._provider, n)
  1273                                                          for n in self._provider.networking.networks
  1274                                                          if n.external and self._check_fip_connectivity(network, n)]
  1275                                                   return ClientPagedResultList(self._provider, igl, limit=limit,
  1276                                                                                marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: get at line 1284

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1284                                               @dispatch(event="provider.networking.floating_ips.get",
  1285                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1286                                               @profile
  1287                                               def get(self, gateway, fip_id):
  1288                                                   try:
  1289                                                       return OpenStackFloatingIP(
  1290                                                           self.provider,
  1291                                                           self.provider.os_conn.network.get_ip(fip_id))
  1292                                                   except (ResourceNotFound, NotFoundException):
  1293                                                       log.debug("Floating IP %s not found.", fip_id)
  1294                                                       return None

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: list at line 1296

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1296                                               @dispatch(event="provider.networking.floating_ips.list",
  1297                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1298                                               @profile
  1299                                               def list(self, gateway, limit=None, marker=None):
  1300                                                   fips = [OpenStackFloatingIP(self.provider, fip)
  1301                                                           for fip in self.provider.os_conn.network.ips(
  1302                                                               floating_network_id=gateway.id
  1303                                                           )]
  1304                                                   return ClientPagedResultList(self.provider, fips,
  1305                                                                                limit=limit, marker=marker)

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: create at line 1307

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1307                                               @dispatch(event="provider.networking.floating_ips.create",
  1308                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1309                                               @profile
  1310                                               def create(self, gateway):
  1311                                                   return OpenStackFloatingIP(
  1312                                                       self.provider, self.provider.os_conn.network.create_ip(
  1313                                                           floating_network_id=gateway.id))

Total time: 0 s
File: /Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py
Function: delete at line 1315

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1315                                               @dispatch(event="provider.networking.floating_ips.delete",
  1316                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1317                                               @profile
  1318                                               def delete(self, gateway, fip):
  1319                                                   if isinstance(fip, OpenStackFloatingIP):
  1320                                                       # pylint:disable=protected-access
  1321                                                       os_ip = fip._ip
  1322                                                   else:
  1323                                                       try:
  1324                                                           os_ip = self.provider.os_conn.network.get_ip(fip)
  1325                                                       except (ResourceNotFound, NotFoundException):
  1326                                                           log.debug("Floating IP %s not found.", fip)
  1327                                                           return True
  1328                                                   os_ip.delete(self._provider.os_conn.session)

