cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase


Test output
 .E.E..
======================================================================
ERROR: test_crud_snapshot (cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 45, in wrap_exception
    return next_handler.invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 110, in invoke
    result = self.callback(*args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/line_profiler.py", line 115, in wrapper
    result = func(*args, **kwds)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py", line 537, in create
    params)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py", line 527, in create_snapshot
    params
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/azure/mgmt/compute/v2018_04_01/operations/snapshots_operations.py", line 127, in create_or_update
    **operation_config
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/azure/mgmt/compute/v2018_04_01/operations/snapshots_operations.py", line 79, in _create_or_update_initial
    raise exp
msrestazure.azure_exceptions.CloudError: Azure Error: NotFound
Message: Resource cb-crudsnap-af95c9-a9af68 is not found.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_block_store_service.py", line 179, in test_crud_snapshot
    "cb-snap", create_snap, cleanup_snap)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/standard_interface_tests.py", line 339, in check_crud
    obj = create_func(label)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_block_store_service.py", line 164, in create_snap
    description=label)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py", line 445, in create_snapshot
    description)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/middleware.py", line 74, in wrapper
    return dispatcher.dispatch(self, event, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 218, in dispatch
    return handlers[0].invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 78, in invoke
    result = self.callback(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 55, in wrap_exception
    six.raise_from(cb_ex, e)
  File "<string>", line 3, in raise_from
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Azure Error: NotFound
Message: Resource cb-crudsnap-af95c9-a9af68 is not found. from exception type: <class 'msrestazure.azure_exceptions.CloudError'>

======================================================================
ERROR: test_snapshot_properties (cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 45, in wrap_exception
    return next_handler.invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 110, in invoke
    result = self.callback(*args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/line_profiler.py", line 115, in wrapper
    result = func(*args, **kwds)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/services.py", line 537, in create
    params)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/azure_client.py", line 527, in create_snapshot
    params
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/azure/mgmt/compute/v2018_04_01/operations/snapshots_operations.py", line 127, in create_or_update
    **operation_config
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/azure/mgmt/compute/v2018_04_01/operations/snapshots_operations.py", line 79, in _create_or_update_initial
    raise exp
msrestazure.azure_exceptions.CloudError: Azure Error: NotFound
Message: Resource cb-snapprop-29bbfa-a87924 is not found.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_block_store_service.py", line 202, in test_snapshot_properties
    description=snap_label)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/azure/resources.py", line 445, in create_snapshot
    description)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/middleware.py", line 74, in wrapper
    return dispatcher.dispatch(self, event, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 218, in dispatch
    return handlers[0].invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 78, in invoke
    result = self.callback(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 55, in wrap_exception
    six.raise_from(cb_ex, e)
  File "<string>", line 3, in raise_from
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Azure Error: NotFound
Message: Resource cb-snapprop-29bbfa-a87924 is not found. from exception type: <class 'msrestazure.azure_exceptions.CloudError'>

----------------------------------------------------------------------
Ran 6 tests in 1006.019s

FAILED (errors=2)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 326.251 s
Function: create at line 863

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   863                                               @dispatch(event="provider.compute.instances.create",
   864                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   865                                               @profile
   866                                               def create(self, label, image, vm_type, subnet, zone,
   867                                                          key_pair=None, vm_firewalls=None, user_data=None,
   868                                                          launch_config=None, **kwargs):
   869         2         30.0     15.0      0.0          AzureInstance.assert_valid_resource_label(label)
   870         2          5.0      2.5      0.0          instance_name = AzureInstance._generate_name_from_label(label,
   871         2         98.0     49.0      0.0                                                                  "cb-ins")
   872                                           
   873         2          5.0      2.5      0.0          image = (image if isinstance(image, AzureMachineImage) else
   874         2        229.0    114.5      0.0                   self.provider.compute.images.get(image))
   875         2          3.0      1.5      0.0          if not isinstance(image, AzureMachineImage):
   876                                                       raise Exception("Provided image %s is not a valid azure image"
   877                                                                       % image)
   878                                           
   879                                                   instance_size = vm_type.id if \
   880         2          6.0      3.0      0.0              isinstance(vm_type, VMType) else vm_type
   881                                           
   882         2          4.0      2.0      0.0          if not subnet:
   883                                                       # Azure has only a single zone per region; use the current one
   884                                                       zone = self.provider.compute.regions.get(
   885                                                           self.provider.region_name).zones[0]
   886                                                       subnet = self.provider.networking.subnets.get_or_create_default(
   887                                                           zone)
   888                                                   else:
   889                                                       subnet = (self.provider.networking.subnets.get(subnet)
   890         2          6.0      3.0      0.0                        if isinstance(subnet, str) else subnet)
   891                                           
   892         2          4.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   893                                           
   894                                                   subnet_id, zone_id, vm_firewall_id = \
   895         2          6.0      3.0      0.0              self._resolve_launch_options(instance_name,
   896         2     986587.0 493293.5      0.3                                           subnet, zone_id, vm_firewalls)
   897                                           
   898         2          5.0      2.5      0.0          storage_profile = self._create_storage_profile(image, launch_config,
   899         2        834.0    417.0      0.0                                                         instance_name, zone_id)
   900                                           
   901                                                   nic_params = {
   902         2          9.0      4.5      0.0              'location': self.provider.region_name,
   903                                                       'ip_configurations': [{
   904         2          4.0      2.0      0.0                  'name': instance_name + '_ip_config',
   905         2          3.0      1.5      0.0                  'private_ip_allocation_method': 'Dynamic',
   906                                                           'subnet': {
   907         2          4.0      2.0      0.0                      'id': subnet_id
   908                                                           }
   909                                                       }]
   910                                                   }
   911                                           
   912         2          4.0      2.0      0.0          if vm_firewall_id:
   913                                                       nic_params['network_security_group'] = {
   914                                                           'id': vm_firewall_id
   915                                                       }
   916         2         15.0      7.5      0.0          nic_info = self.provider.azure_client.create_nic(
   917         2          4.0      2.0      0.0              instance_name + '_nic',
   918         2   63209196.0 31604598.0     19.4              nic_params
   919                                                   )
   920                                                   # #! indicates shell script
   921                                                   ud = '#cloud-config\n' + user_data \
   922         2          6.0      3.0      0.0              if user_data and not user_data.startswith('#!')\
   923                                                       and not user_data.startswith('#cloud-config') else user_data
   924                                           
   925                                                   # Key_pair is mandatory in azure and it should not be None.
   926         2          4.0      2.0      0.0          temp_key_pair = None
   927         2          2.0      1.0      0.0          if key_pair:
   928                                                       key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
   929                                                                   else self.provider.security.key_pairs.get(key_pair))
   930                                                   else:
   931                                                       # Create a temporary keypair if none is provided to keep Azure
   932                                                       # happy, but the private key will be discarded, so it'll be all
   933                                                       # but useless. However, this will allow an instance to be launched
   934                                                       # without specifying a keypair, so users may still be able to login
   935                                                       # if they have a preinstalled keypair/password baked into the image
   936         2          4.0      2.0      0.0              temp_kp_name = "".join(["cb-default-kp-",
   937         2          8.0      4.0      0.0                                     str(uuid.uuid5(uuid.NAMESPACE_OID,
   938         2        136.0     68.0      0.0                                                    instance_name))[-6:]])
   939         2         36.0     18.0      0.0              key_pair = self.provider.security.key_pairs.create(
   940         2   22710659.0 11355329.5      7.0                  name=temp_kp_name)
   941         2          4.0      2.0      0.0              temp_key_pair = key_pair
   942                                           
   943                                                   params = {
   944         2          4.0      2.0      0.0              'location': zone_id or self.provider.region_name,
   945                                                       'os_profile': {
   946         2          9.0      4.5      0.0                  'admin_username': self.provider.vm_default_user_name,
   947         2          3.0      1.5      0.0                  'computer_name': instance_name,
   948                                                           'linux_configuration': {
   949         2          4.0      2.0      0.0                      "disable_password_authentication": True,
   950                                                               "ssh": {
   951         2          2.0      1.0      0.0                          "public_keys": [{
   952                                                                       "path":
   953         2          4.0      2.0      0.0                                  "/home/{}/.ssh/authorized_keys".format(
   954         2          7.0      3.5      0.0                                          self.provider.vm_default_user_name),
   955         2         19.0      9.5      0.0                                  "key_data": key_pair._key_pair.Key
   956                                                                   }]
   957                                                               }
   958                                                           }
   959                                                       },
   960                                                       'hardware_profile': {
   961         2          5.0      2.5      0.0                  'vm_size': instance_size
   962                                                       },
   963                                                       'network_profile': {
   964         2          4.0      2.0      0.0                  'network_interfaces': [{
   965         2          8.0      4.0      0.0                      'id': nic_info.id
   966                                                           }]
   967                                                       },
   968         2          4.0      2.0      0.0              'storage_profile': storage_profile,
   969         2          4.0      2.0      0.0              'tags': {'Label': label}
   970                                                   }
   971                                           
   972         2          7.0      3.5      0.0          for disk_def in storage_profile.get('data_disks', []):
   973                                                       params['tags'] = dict(disk_def.get('tags', {}), **params['tags'])
   974                                           
   975         2          4.0      2.0      0.0          if user_data:
   976                                                       custom_data = base64.b64encode(bytes(ud, 'utf-8'))
   977                                                       params['os_profile']['custom_data'] = str(custom_data, 'utf-8')
   978                                           
   979         2          3.0      1.5      0.0          if not temp_key_pair:
   980                                                       params['tags'].update(Key_Pair=key_pair.id)
   981                                           
   982         2          4.0      2.0      0.0          try:
   983         2  238277139.0 119138569.5     73.0              vm = self.provider.azure_client.create_vm(instance_name, params)
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
   995         2          8.0      4.0      0.0              if temp_key_pair:
   996         2     368600.0 184300.0      0.1                  temp_key_pair.delete()
   997         2     697523.0 348761.5      0.2          return AzureInstance(self.provider, vm)

Total time: 292.517 s
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
  1056         2          2.0      1.0      0.0          if not instance:
  1057                                                       return
  1058                                           
  1059                                                   # Remove IPs first to avoid a network interface conflict
  1060                                                   # pylint:disable=protected-access
  1061         2     732860.0 366430.0      0.3          for public_ip_id in ins._public_ip_ids:
  1062                                                       ins.remove_floating_ip(public_ip_id)
  1063         2  154126743.0 77063371.5     52.7          self.provider.azure_client.deallocate_vm(ins.id)
  1064         2   52998383.0 26499191.5     18.1          self.provider.azure_client.delete_vm(ins.id)
  1065                                                   # pylint:disable=protected-access
  1066         4         28.0      7.0      0.0          for nic_id in ins._nic_ids:
  1067         2   22835045.0 11417522.5      7.8              self.provider.azure_client.delete_nic(nic_id)
  1068                                                   # pylint:disable=protected-access
  1069         2          7.0      3.5      0.0          for data_disk in ins._vm.storage_profile.data_disks:
  1070                                                       if data_disk.managed_disk:
  1071                                                           # pylint:disable=protected-access
  1072                                                           if ins._vm.tags.get('delete_on_terminate',
  1073                                                                               'False') == 'True':
  1074                                                               self.provider.azure_client. \
  1075                                                                   delete_disk(data_disk.managed_disk.id)
  1076                                                   # pylint:disable=protected-access
  1077         2          4.0      2.0      0.0          if ins._vm.storage_profile.os_disk.managed_disk:
  1078         2         17.0      8.5      0.0              self.provider.azure_client. \
  1079         2   61823804.0 30911902.0     21.1                  delete_disk(ins._vm.storage_profile.os_disk.managed_disk.id)

Total time: 161.33 s
Function: create at line 413

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   413                                               @dispatch(event="provider.storage.volumes.create",
   414                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   415                                               @profile
   416                                               def create(self, label, size, zone, snapshot=None, description=None):
   417        15        173.0     11.5      0.0          AzureVolume.assert_valid_resource_label(label)
   418         5        240.0     48.0      0.0          disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
   419         5          6.0      1.2      0.0          tags = {'Label': label}
   420                                           
   421         5          7.0      1.4      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   422                                                   snapshot = (self.provider.storage.snapshots.get(snapshot)
   423         5          4.0      0.8      0.0                      if snapshot and isinstance(snapshot, str) else snapshot)
   424                                           
   425         5          4.0      0.8      0.0          if description:
   426         1          2.0      2.0      0.0              tags.update(Description=description)
   427                                           
   428         5          2.0      0.4      0.0          if snapshot:
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
   445         5          5.0      1.0      0.0                      zone_id or self.provider.region_name,
   446         5          5.0      1.0      0.0                  'disk_size_gb': size,
   447                                                           'creation_data': {
   448         5         14.0      2.8      0.0                      'create_option': DiskCreateOption.empty
   449                                                           },
   450         5          7.0      1.4      0.0                  'tags': tags
   451                                                       }
   452                                           
   453         5    1059871.0 211974.2      0.7              disk = self.provider.azure_client.create_empty_disk(disk_name,
   454         5  156255105.0 31251021.0     96.9                                                                  params)
   455                                           
   456         5    4014558.0 802911.6      2.5          azure_vol = self.provider.azure_client.get_disk(disk.id)
   457         5        123.0     24.6      0.0          cb_vol = AzureVolume(self.provider, azure_vol)
   458                                           
   459         5          6.0      1.2      0.0          return cb_vol

Total time: 156.372 s
Function: delete at line 461

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   461                                               @dispatch(event="provider.storage.volumes.delete",
   462                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   463                                               @profile
   464                                               def delete(self, volume_id):
   465         5         21.0      4.2      0.0          vol_id = (volume_id.id if isinstance(volume_id, AzureVolume)
   466                                                             else volume_id)
   467         5  156372385.0 31274477.0    100.0          self.provider.azure_client.delete_disk(vol_id)

Total time: 22.6894 s
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.key_pairs.create",
   307                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, name, public_key_material=None):
   310         2         26.0     13.0      0.0          AzureKeyPair.assert_valid_resource_name(name)
   311         2   22008812.0 11004406.0     97.0          key_pair = self.get(name)
   312                                           
   313         2          1.0      0.5      0.0          if key_pair:
   314                                                       raise DuplicateResourceException(
   315                                                           'Keypair already exists with name {0}'.format(name))
   316                                           
   317         2          2.0      1.0      0.0          private_key = None
   318         2          2.0      1.0      0.0          if not public_key_material:
   319         2     170174.0  85087.0      0.8              public_key_material, private_key = cb_helpers.generate_key_pair()
   320                                           
   321                                                   entity = {
   322         2          9.0      4.5      0.0              'PartitionKey': AzureKeyPairService.PARTITION_KEY,
   323         2         69.0     34.5      0.0              'RowKey': str(uuid.uuid4()),
   324         2          1.0      0.5      0.0              'Name': name,
   325         2          4.0      2.0      0.0              'Key': public_key_material
   326                                                   }
   327                                           
   328         2     253106.0 126553.0      1.1          self.provider.azure_client.create_public_key(entity)
   329         2     257143.0 128571.5      1.1          key_pair = self.get(name)
   330         2          5.0      2.5      0.0          key_pair.material = private_key
   331         2          1.0      0.5      0.0          return key_pair

Total time: 22.2458 s
Function: get at line 259

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   259                                               @dispatch(event="provider.security.key_pairs.get",
   260                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   261                                               @profile
   262                                               def get(self, key_pair_id):
   263         4          5.0      1.2      0.0          try:
   264         4         30.0      7.5      0.0              key_pair = self.provider.azure_client.\
   265         4   22245719.0 5561429.8    100.0                  get_public_key(key_pair_id)
   266                                           
   267         4          7.0      1.8      0.0              if key_pair:
   268         2         42.0     21.0      0.0                  return AzureKeyPair(self.provider, key_pair)
   269         2          0.0      0.0      0.0              return None
   270                                                   except AzureException as error:
   271                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   272                                                       log.debug(error)
   273                                                       return None

Total time: 19.3186 s
Function: refresh at line 452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   452                                               @profile
   453                                               def refresh(self):
   454                                                   """
   455                                                   Refreshes the state of this volume by re-querying the cloud provider
   456                                                   for its latest state.
   457                                                   """
   458        35        144.0      4.1      0.0          try:
   459        35        487.0     13.9      0.0              self._volume = self._provider.azure_client. \
   460        35   19317560.0 551930.3    100.0                  get_disk(self.id)
   461        33        176.0      5.3      0.0              self._update_state()
   462         2          6.0      3.0      0.0          except (CloudError, ValueError) as cloud_error:
   463         2        249.0    124.5      0.0              log.exception(cloud_error.message)
   464                                                       # The volume no longer exists and cannot be refreshed.
   465                                                       # set the state to unknown
   466         2          4.0      2.0      0.0              self._state = 'unknown'

Total time: 3.50781 s
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323         2    3507803.0 1753901.5    100.0          matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324         2          2.0      1.0      0.0          if matches:
   325         2          3.0      1.5      0.0              return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 3.43614 s
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276         2    2276552.0 1138276.0     66.3          obj_list = self._list_subnets(network)
  1277         2          7.0      3.5      0.0          filters = ['label']
  1278         2    1159514.0 579757.0     33.7          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280         2          5.0      2.5      0.0          return ClientPagedResultList(self.provider,
  1281         2         64.0     32.0      0.0                                       matches if matches else [])

Total time: 2.28898 s
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
   361        12        162.0     13.5      0.0          self.assert_valid_resource_label(value)
   362         4         13.0      3.2      0.0          self._volume.tags.update(Label=value or "")
   363         4         46.0     11.5      0.0          self._provider.azure_client. \
   364         4          6.0      1.5      0.0              update_disk_tags(self.id,
   365         4    2288758.0 572189.5    100.0                               self._volume.tags)

Total time: 1.69307 s
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172         6          6.0      1.0      0.0          try:
  1173         6    1692916.0 282152.7    100.0              network = self.provider.azure_client.get_network(network_id)
  1174         6        148.0     24.7      0.0              return AzureNetwork(self.provider, network)
  1175                                                   except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177                                                       log.exception(cloud_error)
  1178                                                       return None

Total time: 1.55794 s
Function: create at line 512

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   512                                               @dispatch(event="provider.storage.snapshots.create",
   513                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   514                                               @profile
   515                                               def create(self, label, volume, description=None):
   516        12        207.0     17.2      0.0          AzureSnapshot.assert_valid_resource_label(label)
   517         2          4.0      2.0      0.0          snapshot_name = AzureSnapshot._generate_name_from_label(label,
   518         2         90.0     45.0      0.0                                                                  "cb-snap")
   519         2          4.0      2.0      0.0          tags = {'Label': label}
   520         2          1.0      0.5      0.0          if description:
   521         2          4.0      2.0      0.0              tags.update(Description=description)
   522                                           
   523                                                   volume = (self.provider.storage.volumes.get(volume)
   524         2          5.0      2.5      0.0                    if isinstance(volume, str) else volume)
   525                                           
   526                                                   params = {
   527         2         17.0      8.5      0.0              'location': self.provider.azure_client.region_name,
   528                                                       'creation_data': {
   529         2          6.0      3.0      0.0                  'create_option': DiskCreateOption.copy,
   530         2          6.0      3.0      0.0                  'source_uri': volume.resource_id
   531                                                       },
   532         2          4.0      2.0      0.0              'disk_size_gb': volume.size,
   533         2          2.0      1.0      0.0              'tags': tags
   534                                                   }
   535                                           
   536         2          5.0      2.5      0.0          azure_snap = self.provider.azure_client.create_snapshot(snapshot_name,
   537         2    1557587.0 778793.5    100.0                                                                  params)
   538                                                   return AzureSnapshot(self.provider, azure_snap)

Total time: 1.44535 s
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184         2          3.0      1.5      0.0          networks = [AzureNetwork(self.provider, network)
  1185         2    1445222.0 722611.0    100.0                      for network in self.provider.azure_client.list_networks()]
  1186         2         11.0      5.5      0.0          return ClientPagedResultList(self.provider, networks,
  1187         2        110.0     55.0      0.0                                       limit=limit, marker=marker)

Total time: 1.24565 s
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342                                                   """
  1343                                                   Refreshes the state of this instance by re-querying the cloud provider
  1344                                                   for its latest state.
  1345                                                   """
  1346         4         10.0      2.5      0.0          try:
  1347         4    1245282.0 311320.5    100.0              self._vm = self._provider.azure_client.get_vm(self.id)
  1348         2          4.0      2.0      0.0              if not self._vm.tags:
  1349                                                           self._vm.tags = {}
  1350         2         13.0      6.5      0.0              self._update_state()
  1351         2          6.0      3.0      0.0          except (CloudError, ValueError) as cloud_error:
  1352         2        328.0    164.0      0.0              log.exception(cloud_error.message)
  1353                                                       # The volume no longer exists and cannot be refreshed.
  1354                                                       # set the state to unknown
  1355         2          4.0      2.0      0.0              self._state = 'unknown'

Total time: 1.02974 s
Function: list at line 404

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   404                                               @dispatch(event="provider.storage.volumes.list",
   405                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   406                                               @profile
   407                                               def list(self, limit=None, marker=None):
   408         6       2733.0    455.5      0.3          azure_vols = self.provider.azure_client.list_disks()
   409         6    1026775.0 171129.2     99.7          cb_vols = [AzureVolume(self.provider, vol) for vol in azure_vols]
   410         6         20.0      3.3      0.0          return ClientPagedResultList(self.provider, cb_vols,
   411         6        216.0     36.0      0.0                                       limit=limit, marker=marker)

Total time: 0.514181 s
Function: get at line 375

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   375                                               @dispatch(event="provider.storage.volumes.get",
   376                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   377                                               @profile
   378                                               def get(self, volume_id):
   379         2          1.0      0.5      0.0          try:
   380         2     514031.0 257015.5    100.0              volume = self.provider.azure_client.get_disk(volume_id)
   381         1         18.0     18.0      0.0              return AzureVolume(self.provider, volume)
   382         1          3.0      3.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
   383                                                       # Azure raises the cloud error if the resource not available
   384         1        127.0    127.0      0.0              log.exception(cloud_error)
   385         1          1.0      1.0      0.0              return None

Total time: 0.406326 s
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113         2          3.0      1.5      0.0          region = None
  1114         6     406215.0  67702.5    100.0          for azureRegion in self.provider.azure_client.list_locations():
  1115         6          7.0      1.2      0.0              if azureRegion.name == region_id:
  1116         2         37.0     18.5      0.0                  region = AzureRegion(self.provider, azureRegion)
  1117         2         62.0     31.0      0.0                  break
  1118         2          2.0      1.0      0.0          return region

Total time: 0.346711 s
Function: delete at line 333

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   333                                               @dispatch(event="provider.security.key_pairs.delete",
   334                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   335                                               @profile
   336                                               def delete(self, key_pair):
   337         2          4.0      2.0      0.0          key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
   338                                                               self.get(key_pair))
   339         2          3.0      1.5      0.0          if key_pair:
   340                                                       # pylint:disable=protected-access
   341         2     346704.0 173352.0    100.0              self.provider.azure_client.delete_public_key(key_pair._key_pair)

Total time: 0.346307 s
Function: find at line 387

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   387                                               @dispatch(event="provider.storage.volumes.find",
   388                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   389                                               @profile
   390                                               def find(self, **kwargs):
   391         3          2.0      0.7      0.0          obj_list = self
   392         3          2.0      0.7      0.0          filters = ['label']
   393         3     346247.0 115415.7    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   394                                           
   395                                                   # All kwargs should have been popped at this time.
   396         2          3.0      1.5      0.0          if len(kwargs) > 0:
   397                                                       raise InvalidParamException(
   398                                                           "Unrecognised parameters for search: %s. Supported "
   399                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
   400                                           
   401         2          4.0      2.0      0.0          return ClientPagedResultList(self.provider,
   402         2         49.0     24.5      0.0                                       matches if matches else [])

Total time: 0.000192 s
Function: get at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @profile
   678                                               def get(self, image_id):
   679                                                   """
   680                                                   Returns an Image given its id
   681                                                   """
   682         2          1.0      0.5      0.5          try:
   683         2        157.0     78.5     81.8              image = self.provider.azure_client.get_image(image_id)
   684         2         34.0     17.0     17.7              return AzureMachineImage(self.provider, image)
   685                                                   except (CloudError, InvalidValueException) as cloud_error:
   686                                                       # Azure raises the cloud error if the resource not available
   687                                                       log.exception(cloud_error)
   688                                                       return None

