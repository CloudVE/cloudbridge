cloudbridge.test.test_image_service.CloudImageServiceTestCase


Test output
 ..
----------------------------------------------------------------------
Ran 2 tests in 735.237s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 302.637 s
Function: create at line 863

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   863                                               @dispatch(event="provider.compute.instances.create",
   864                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   865                                               @profile
   866                                               def create(self, label, image, vm_type, subnet, zone,
   867                                                          key_pair=None, vm_firewalls=None, user_data=None,
   868                                                          launch_config=None, **kwargs):
   869         2         38.0     19.0      0.0          AzureInstance.assert_valid_resource_label(label)
   870         2          6.0      3.0      0.0          instance_name = AzureInstance._generate_name_from_label(label,
   871         2        112.0     56.0      0.0                                                                  "cb-ins")
   872                                           
   873         2          6.0      3.0      0.0          image = (image if isinstance(image, AzureMachineImage) else
   874         1        149.0    149.0      0.0                   self.provider.compute.images.get(image))
   875         2          4.0      2.0      0.0          if not isinstance(image, AzureMachineImage):
   876                                                       raise Exception("Provided image %s is not a valid azure image"
   877                                                                       % image)
   878                                           
   879                                                   instance_size = vm_type.id if \
   880         2          9.0      4.5      0.0              isinstance(vm_type, VMType) else vm_type
   881                                           
   882         2          4.0      2.0      0.0          if not subnet:
   883                                                       # Azure has only a single zone per region; use the current one
   884                                                       zone = self.provider.compute.regions.get(
   885                                                           self.provider.region_name).zones[0]
   886                                                       subnet = self.provider.networking.subnets.get_or_create_default(
   887                                                           zone)
   888                                                   else:
   889                                                       subnet = (self.provider.networking.subnets.get(subnet)
   890         2          8.0      4.0      0.0                        if isinstance(subnet, str) else subnet)
   891                                           
   892         2          4.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   893                                           
   894                                                   subnet_id, zone_id, vm_firewall_id = \
   895         2          7.0      3.5      0.0              self._resolve_launch_options(instance_name,
   896         2     863326.0 431663.0      0.3                                           subnet, zone_id, vm_firewalls)
   897                                           
   898         2          5.0      2.5      0.0          storage_profile = self._create_storage_profile(image, launch_config,
   899         2        509.0    254.5      0.0                                                         instance_name, zone_id)
   900                                           
   901                                                   nic_params = {
   902         2         11.0      5.5      0.0              'location': self.provider.region_name,
   903                                                       'ip_configurations': [{
   904         2          3.0      1.5      0.0                  'name': instance_name + '_ip_config',
   905         2          2.0      1.0      0.0                  'private_ip_allocation_method': 'Dynamic',
   906                                                           'subnet': {
   907         2          4.0      2.0      0.0                      'id': subnet_id
   908                                                           }
   909                                                       }]
   910                                                   }
   911                                           
   912         2          3.0      1.5      0.0          if vm_firewall_id:
   913                                                       nic_params['network_security_group'] = {
   914                                                           'id': vm_firewall_id
   915                                                       }
   916         2         16.0      8.0      0.0          nic_info = self.provider.azure_client.create_nic(
   917         2          4.0      2.0      0.0              instance_name + '_nic',
   918         2   63373404.0 31686702.0     20.9              nic_params
   919                                                   )
   920                                                   # #! indicates shell script
   921                                                   ud = '#cloud-config\n' + user_data \
   922         2          6.0      3.0      0.0              if user_data and not user_data.startswith('#!')\
   923                                                       and not user_data.startswith('#cloud-config') else user_data
   924                                           
   925                                                   # Key_pair is mandatory in azure and it should not be None.
   926         2          2.0      1.0      0.0          temp_key_pair = None
   927         2          3.0      1.5      0.0          if key_pair:
   928                                                       key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
   929                                                                   else self.provider.security.key_pairs.get(key_pair))
   930                                                   else:
   931                                                       # Create a temporary keypair if none is provided to keep Azure
   932                                                       # happy, but the private key will be discarded, so it'll be all
   933                                                       # but useless. However, this will allow an instance to be launched
   934                                                       # without specifying a keypair, so users may still be able to login
   935                                                       # if they have a preinstalled keypair/password baked into the image
   936         2          4.0      2.0      0.0              temp_kp_name = "".join(["cb-default-kp-",
   937         2          6.0      3.0      0.0                                     str(uuid.uuid5(uuid.NAMESPACE_OID,
   938         2        123.0     61.5      0.0                                                    instance_name))[-6:]])
   939         2         39.0     19.5      0.0              key_pair = self.provider.security.key_pairs.create(
   940         2    2467166.0 1233583.0      0.8                  name=temp_kp_name)
   941         2          4.0      2.0      0.0              temp_key_pair = key_pair
   942                                           
   943                                                   params = {
   944         2          4.0      2.0      0.0              'location': zone_id or self.provider.region_name,
   945                                                       'os_profile': {
   946         2         12.0      6.0      0.0                  'admin_username': self.provider.vm_default_user_name,
   947         2          4.0      2.0      0.0                  'computer_name': instance_name,
   948                                                           'linux_configuration': {
   949         2          4.0      2.0      0.0                      "disable_password_authentication": True,
   950                                                               "ssh": {
   951         2          3.0      1.5      0.0                          "public_keys": [{
   952                                                                       "path":
   953         2          4.0      2.0      0.0                                  "/home/{}/.ssh/authorized_keys".format(
   954         2          8.0      4.0      0.0                                          self.provider.vm_default_user_name),
   955         2         25.0     12.5      0.0                                  "key_data": key_pair._key_pair.Key
   956                                                                   }]
   957                                                               }
   958                                                           }
   959                                                       },
   960                                                       'hardware_profile': {
   961         2          8.0      4.0      0.0                  'vm_size': instance_size
   962                                                       },
   963                                                       'network_profile': {
   964         2          4.0      2.0      0.0                  'network_interfaces': [{
   965         2          8.0      4.0      0.0                      'id': nic_info.id
   966                                                           }]
   967                                                       },
   968         2          4.0      2.0      0.0              'storage_profile': storage_profile,
   969         2          6.0      3.0      0.0              'tags': {'Label': label}
   970                                                   }
   971                                           
   972         2          6.0      3.0      0.0          for disk_def in storage_profile.get('data_disks', []):
   973                                                       params['tags'] = dict(disk_def.get('tags', {}), **params['tags'])
   974                                           
   975         2          4.0      2.0      0.0          if user_data:
   976                                                       custom_data = base64.b64encode(bytes(ud, 'utf-8'))
   977                                                       params['os_profile']['custom_data'] = str(custom_data, 'utf-8')
   978                                           
   979         2          4.0      2.0      0.0          if not temp_key_pair:
   980                                                       params['tags'].update(Key_Pair=key_pair.id)
   981                                           
   982         2          3.0      1.5      0.0          try:
   983         2  234547650.0 117273825.0     77.5              vm = self.provider.azure_client.create_vm(instance_name, params)
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
   995         2          7.0      3.5      0.0              if temp_key_pair:
   996         2     514491.0 257245.5      0.2                  temp_key_pair.delete()
   997         2     869810.0 434905.0      0.3          return AzureInstance(self.provider, vm)

Total time: 193.572 s
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
  1054         2          5.0      2.5      0.0          ins = (instance if isinstance(instance, AzureInstance) else
  1055                                                          self.get(instance))
  1056         2          1.0      0.5      0.0          if not instance:
  1057                                                       return
  1058                                           
  1059                                                   # Remove IPs first to avoid a network interface conflict
  1060                                                   # pylint:disable=protected-access
  1061         2     629624.0 314812.0      0.3          for public_ip_id in ins._public_ip_ids:
  1062                                                       ins.remove_floating_ip(public_ip_id)
  1063         2   57140854.0 28570427.0     29.5          self.provider.azure_client.deallocate_vm(ins.id)
  1064         2   52038863.0 26019431.5     26.9          self.provider.azure_client.delete_vm(ins.id)
  1065                                                   # pylint:disable=protected-access
  1066         4         33.0      8.2      0.0          for nic_id in ins._nic_ids:
  1067         2   22277030.0 11138515.0     11.5              self.provider.azure_client.delete_nic(nic_id)
  1068                                                   # pylint:disable=protected-access
  1069         2         14.0      7.0      0.0          for data_disk in ins._vm.storage_profile.data_disks:
  1070                                                       if data_disk.managed_disk:
  1071                                                           # pylint:disable=protected-access
  1072                                                           if ins._vm.tags.get('delete_on_terminate',
  1073                                                                               'False') == 'True':
  1074                                                               self.provider.azure_client. \
  1075                                                                   delete_disk(data_disk.managed_disk.id)
  1076                                                   # pylint:disable=protected-access
  1077         2          3.0      1.5      0.0          if ins._vm.storage_profile.os_disk.managed_disk:
  1078         2         22.0     11.0      0.0              self.provider.azure_client. \
  1079         2   61486021.0 30743010.5     31.8                  delete_disk(ins._vm.storage_profile.os_disk.managed_disk.id)

Total time: 93.7213 s
Function: label at line 629

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   629                                               @label.setter
   630                                               @profile
   631                                               def label(self, value):
   632                                                   """
   633                                                   Set the image label when it is a private image.
   634                                                   """
   635        11         35.0      3.2      0.0          if not self.is_gallery_image:
   636        11        159.0     14.5      0.0              self.assert_valid_resource_label(value)
   637         3         10.0      3.3      0.0              self._image.tags.update(Label=value or "")
   638         3         21.0      7.0      0.0              self._provider.azure_client. \
   639         3   93721100.0 31240366.7    100.0                  update_image_tags(self.id, self._image.tags)

Total time: 2.4564 s
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.key_pairs.create",
   307                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, name, public_key_material=None):
   310         2         26.0     13.0      0.0          AzureKeyPair.assert_valid_resource_name(name)
   311         2    1818893.0 909446.5     74.0          key_pair = self.get(name)
   312                                           
   313         2          1.0      0.5      0.0          if key_pair:
   314                                                       raise DuplicateResourceException(
   315                                                           'Keypair already exists with name {0}'.format(name))
   316                                           
   317         2          2.0      1.0      0.0          private_key = None
   318         2          1.0      0.5      0.0          if not public_key_material:
   319         2     125367.0  62683.5      5.1              public_key_material, private_key = cb_helpers.generate_key_pair()
   320                                           
   321                                                   entity = {
   322         2          8.0      4.0      0.0              'PartitionKey': AzureKeyPairService.PARTITION_KEY,
   323         2         69.0     34.5      0.0              'RowKey': str(uuid.uuid4()),
   324         2          2.0      1.0      0.0              'Name': name,
   325         2          2.0      1.0      0.0              'Key': public_key_material
   326                                                   }
   327                                           
   328         2     259619.0 129809.5     10.6          self.provider.azure_client.create_public_key(entity)
   329         2     252398.0 126199.0     10.3          key_pair = self.get(name)
   330         2          6.0      3.0      0.0          key_pair.material = private_key
   331         2          1.0      0.5      0.0          return key_pair

Total time: 2.12995 s
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323         1    2129945.0 2129945.0    100.0          matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324         1          1.0      1.0      0.0          if matches:
   325         1          2.0      2.0      0.0              return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 2.07273 s
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276         1    1595752.0 1595752.0     77.0          obj_list = self._list_subnets(network)
  1277         1          5.0      5.0      0.0          filters = ['label']
  1278         1     476932.0 476932.0     23.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280         1          5.0      5.0      0.0          return ClientPagedResultList(self.provider,
  1281         1         34.0     34.0      0.0                                       matches if matches else [])

Total time: 2.05943 s
Function: get at line 259

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   259                                               @dispatch(event="provider.security.key_pairs.get",
   260                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   261                                               @profile
   262                                               def get(self, key_pair_id):
   263         4          4.0      1.0      0.0          try:
   264         4         29.0      7.2      0.0              key_pair = self.provider.azure_client.\
   265         4    2059336.0 514834.0    100.0                  get_public_key(key_pair_id)
   266                                           
   267         4          8.0      2.0      0.0              if key_pair:
   268         2         47.0     23.5      0.0                  return AzureKeyPair(self.provider, key_pair)
   269         2          2.0      1.0      0.0              return None
   270                                                   except AzureException as error:
   271                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   272                                                       log.debug(error)
   273                                                       return None

Total time: 1.54248 s
Function: list at line 705

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   705                                               @profile
   706                                               def list(self, filter_by_owner=True, limit=None, marker=None):
   707                                                   """
   708                                                   List all images.
   709                                                   """
   710         6    1542134.0 257022.3    100.0          azure_images = self.provider.azure_client.list_images()
   711                                                   azure_gallery_refs = self.provider.azure_client.list_gallery_refs() \
   712         6         13.0      2.2      0.0              if not filter_by_owner else []
   713         6          8.0      1.3      0.0          cb_images = [AzureMachineImage(self.provider, img)
   714         6        107.0     17.8      0.0                       for img in azure_images + azure_gallery_refs]
   715         6         12.0      2.0      0.0          return ClientPagedResultList(self.provider, cb_images,
   716         6        206.0     34.3      0.0                                       limit=limit, marker=marker)

Total time: 1.36268 s
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342                                                   """
  1343                                                   Refreshes the state of this instance by re-querying the cloud provider
  1344                                                   for its latest state.
  1345                                                   """
  1346         4         13.0      3.2      0.0          try:
  1347         4    1362322.0 340580.5    100.0              self._vm = self._provider.azure_client.get_vm(self.id)
  1348         2          4.0      2.0      0.0              if not self._vm.tags:
  1349                                                           self._vm.tags = {}
  1350         2         10.0      5.0      0.0              self._update_state()
  1351         2          7.0      3.5      0.0          except (CloudError, ValueError) as cloud_error:
  1352         2        316.0    158.0      0.0              log.exception(cloud_error.message)
  1353                                                       # The volume no longer exists and cannot be refreshed.
  1354                                                       # set the state to unknown
  1355         2         10.0      5.0      0.0              self._state = 'unknown'

Total time: 1.26517 s
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184         1          2.0      2.0      0.0          networks = [AzureNetwork(self.provider, network)
  1185         1    1265074.0 1265074.0    100.0                      for network in self.provider.azure_client.list_networks()]
  1186         1          8.0      8.0      0.0          return ClientPagedResultList(self.provider, networks,
  1187         1         88.0     88.0      0.0                                       limit=limit, marker=marker)

Total time: 1.04684 s
Function: refresh at line 705

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   705                                               @profile
   706                                               def refresh(self):
   707                                                   """
   708                                                   Refreshes the state of this instance by re-querying the cloud provider
   709                                                   for its latest state.
   710                                                   """
   711         4         17.0      4.2      0.0          if not self.is_gallery_image:
   712         4          8.0      2.0      0.0              try:
   713         4    1046459.0 261614.8    100.0                  self._image = self._provider.azure_client.get_image(self.id)
   714         2         11.0      5.5      0.0                  self._state = self._image.provisioning_state
   715         2          9.0      4.5      0.0              except CloudError as cloud_error:
   716         2        328.0    164.0      0.0                  log.exception(cloud_error.message)
   717                                                           # image no longer exists
   718         2          8.0      4.0      0.0                  self._state = "unknown"

Total time: 1.02779 s
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172         4          5.0      1.2      0.0          try:
  1173         4    1027667.0 256916.8    100.0              network = self.provider.azure_client.get_network(network_id)
  1174         4        118.0     29.5      0.0              return AzureNetwork(self.provider, network)
  1175                                                   except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177                                                       log.exception(cloud_error)
  1178                                                       return None

Total time: 0.75888 s
Function: get at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @profile
   678                                               def get(self, image_id):
   679                                                   """
   680                                                   Returns an Image given its id
   681                                                   """
   682         3          3.0      1.0      0.0          try:
   683         3     758580.0 252860.0    100.0              image = self.provider.azure_client.get_image(image_id)
   684         2         45.0     22.5      0.0              return AzureMachineImage(self.provider, image)
   685         1          3.0      3.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
   686                                                       # Azure raises the cloud error if the resource not available
   687         1        248.0    248.0      0.0              log.exception(cloud_error)
   688         1          1.0      1.0      0.0              return None

Total time: 0.503087 s
Function: delete at line 333

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   333                                               @dispatch(event="provider.security.key_pairs.delete",
   334                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   335                                               @profile
   336                                               def delete(self, key_pair):
   337         2          4.0      2.0      0.0          key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
   338                                                               self.get(key_pair))
   339         2          2.0      1.0      0.0          if key_pair:
   340                                                       # pylint:disable=protected-access
   341         2     503081.0 251540.5    100.0              self.provider.azure_client.delete_public_key(key_pair._key_pair)

Total time: 0.470769 s
Function: find at line 690

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   690                                               @profile
   691                                               def find(self, **kwargs):
   692         3          1.0      0.3      0.0          obj_list = self
   693         3          2.0      0.7      0.0          filters = ['label']
   694         3     470713.0 156904.3    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   695                                           
   696                                                   # All kwargs should have been popped at this time.
   697         2          3.0      1.5      0.0          if len(kwargs) > 0:
   698                                                       raise InvalidParamException(
   699                                                           "Unrecognised parameters for search: %s. Supported "
   700                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   701                                           
   702         2          3.0      1.5      0.0          return ClientPagedResultList(self.provider,
   703         2         47.0     23.5      0.0                                       matches if matches else [])

Total time: 0.286981 s
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113         2          2.0      1.0      0.0          region = None
  1114         6     286832.0  47805.3     99.9          for azureRegion in self.provider.azure_client.list_locations():
  1115         6          7.0      1.2      0.0              if azureRegion.name == region_id:
  1116         2         67.0     33.5      0.0                  region = AzureRegion(self.provider, azureRegion)
  1117         2         73.0     36.5      0.0                  break
  1118         2          0.0      0.0      0.0          return region

