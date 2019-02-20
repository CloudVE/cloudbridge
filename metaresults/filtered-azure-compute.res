cloudbridge.test.test_compute_service.CloudComputeServiceTestCase


Error during cleanup: 'NoneType' object has no attribute '_ip'
Test output
 E.....
======================================================================
ERROR: test_block_device_mapping_attachments (cloudbridge.test.test_compute_service.CloudComputeServiceTestCase)
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
Message: Resource cb-blkattch-6797b5-607ed5 is not found.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_compute_service.py", line 250, in test_block_device_mapping_attachments
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
Message: Resource cb-blkattch-6797b5-607ed5 is not found. from exception type: <class 'msrestazure.azure_exceptions.CloudError'>

----------------------------------------------------------------------
Ran 6 tests in 1695.659s

FAILED (errors=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 506.829 s
Function: create at line 863

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   863                                               @dispatch(event="provider.compute.instances.create",
   864                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   865                                               @profile
   866                                               def create(self, label, image, vm_type, subnet, zone,
   867                                                          key_pair=None, vm_firewalls=None, user_data=None,
   868                                                          launch_config=None, **kwargs):
   869        13        299.0     23.0      0.0          AzureInstance.assert_valid_resource_label(label)
   870         3         10.0      3.3      0.0          instance_name = AzureInstance._generate_name_from_label(label,
   871         3        150.0     50.0      0.0                                                                  "cb-ins")
   872                                           
   873         3          8.0      2.7      0.0          image = (image if isinstance(image, AzureMachineImage) else
   874         3        317.0    105.7      0.0                   self.provider.compute.images.get(image))
   875         3          7.0      2.3      0.0          if not isinstance(image, AzureMachineImage):
   876                                                       raise Exception("Provided image %s is not a valid azure image"
   877                                                                       % image)
   878                                           
   879                                                   instance_size = vm_type.id if \
   880         3         13.0      4.3      0.0              isinstance(vm_type, VMType) else vm_type
   881                                           
   882         3          6.0      2.0      0.0          if not subnet:
   883                                                       # Azure has only a single zone per region; use the current one
   884                                                       zone = self.provider.compute.regions.get(
   885                                                           self.provider.region_name).zones[0]
   886                                                       subnet = self.provider.networking.subnets.get_or_create_default(
   887                                                           zone)
   888                                                   else:
   889                                                       subnet = (self.provider.networking.subnets.get(subnet)
   890         3         39.0     13.0      0.0                        if isinstance(subnet, str) else subnet)
   891                                           
   892         3          7.0      2.3      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   893                                           
   894                                                   subnet_id, zone_id, vm_firewall_id = \
   895         3          7.0      2.3      0.0              self._resolve_launch_options(instance_name,
   896         3    1338948.0 446316.0      0.3                                           subnet, zone_id, vm_firewalls)
   897                                           
   898         3          8.0      2.7      0.0          storage_profile = self._create_storage_profile(image, launch_config,
   899         3       1155.0    385.0      0.0                                                         instance_name, zone_id)
   900                                           
   901                                                   nic_params = {
   902         3         17.0      5.7      0.0              'location': self.provider.region_name,
   903                                                       'ip_configurations': [{
   904         3          4.0      1.3      0.0                  'name': instance_name + '_ip_config',
   905         3          4.0      1.3      0.0                  'private_ip_allocation_method': 'Dynamic',
   906                                                           'subnet': {
   907         3          6.0      2.0      0.0                      'id': subnet_id
   908                                                           }
   909                                                       }]
   910                                                   }
   911                                           
   912         3          5.0      1.7      0.0          if vm_firewall_id:
   913                                                       nic_params['network_security_group'] = {
   914         1          1.0      1.0      0.0                  'id': vm_firewall_id
   915                                                       }
   916         3         20.0      6.7      0.0          nic_info = self.provider.azure_client.create_nic(
   917         3          4.0      1.3      0.0              instance_name + '_nic',
   918         3   97431330.0 32477110.0     19.2              nic_params
   919                                                   )
   920                                                   # #! indicates shell script
   921                                                   ud = '#cloud-config\n' + user_data \
   922         3         10.0      3.3      0.0              if user_data and not user_data.startswith('#!')\
   923                                                       and not user_data.startswith('#cloud-config') else user_data
   924                                           
   925                                                   # Key_pair is mandatory in azure and it should not be None.
   926         3          5.0      1.7      0.0          temp_key_pair = None
   927         3          6.0      2.0      0.0          if key_pair:
   928         1          3.0      3.0      0.0              key_pair = (key_pair if isinstance(key_pair, AzureKeyPair)
   929                                                                   else self.provider.security.key_pairs.get(key_pair))
   930                                                   else:
   931                                                       # Create a temporary keypair if none is provided to keep Azure
   932                                                       # happy, but the private key will be discarded, so it'll be all
   933                                                       # but useless. However, this will allow an instance to be launched
   934                                                       # without specifying a keypair, so users may still be able to login
   935                                                       # if they have a preinstalled keypair/password baked into the image
   936         2          8.0      4.0      0.0              temp_kp_name = "".join(["cb-default-kp-",
   937         2          9.0      4.5      0.0                                     str(uuid.uuid5(uuid.NAMESPACE_OID,
   938         2        164.0     82.0      0.0                                                    instance_name))[-6:]])
   939         2         37.0     18.5      0.0              key_pair = self.provider.security.key_pairs.create(
   940         2    6471263.0 3235631.5      1.3                  name=temp_kp_name)
   941         2          3.0      1.5      0.0              temp_key_pair = key_pair
   942                                           
   943                                                   params = {
   944         3          6.0      2.0      0.0              'location': zone_id or self.provider.region_name,
   945                                                       'os_profile': {
   946         3         19.0      6.3      0.0                  'admin_username': self.provider.vm_default_user_name,
   947         3          5.0      1.7      0.0                  'computer_name': instance_name,
   948                                                           'linux_configuration': {
   949         3          4.0      1.3      0.0                      "disable_password_authentication": True,
   950                                                               "ssh": {
   951         3          5.0      1.7      0.0                          "public_keys": [{
   952                                                                       "path":
   953         3          6.0      2.0      0.0                                  "/home/{}/.ssh/authorized_keys".format(
   954         3         13.0      4.3      0.0                                          self.provider.vm_default_user_name),
   955         3         25.0      8.3      0.0                                  "key_data": key_pair._key_pair.Key
   956                                                                   }]
   957                                                               }
   958                                                           }
   959                                                       },
   960                                                       'hardware_profile': {
   961         3          6.0      2.0      0.0                  'vm_size': instance_size
   962                                                       },
   963                                                       'network_profile': {
   964         3          5.0      1.7      0.0                  'network_interfaces': [{
   965         3         10.0      3.3      0.0                      'id': nic_info.id
   966                                                           }]
   967                                                       },
   968         3          4.0      1.3      0.0              'storage_profile': storage_profile,
   969         3          7.0      2.3      0.0              'tags': {'Label': label}
   970                                                   }
   971                                           
   972         3         13.0      4.3      0.0          for disk_def in storage_profile.get('data_disks', []):
   973                                                       params['tags'] = dict(disk_def.get('tags', {}), **params['tags'])
   974                                           
   975         3          5.0      1.7      0.0          if user_data:
   976                                                       custom_data = base64.b64encode(bytes(ud, 'utf-8'))
   977                                                       params['os_profile']['custom_data'] = str(custom_data, 'utf-8')
   978                                           
   979         3          5.0      1.7      0.0          if not temp_key_pair:
   980         1          8.0      8.0      0.0              params['tags'].update(Key_Pair=key_pair.id)
   981                                           
   982         3          5.0      1.7      0.0          try:
   983         3  400185160.0 133395053.3     79.0              vm = self.provider.azure_client.create_vm(instance_name, params)
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
   995         3         11.0      3.7      0.0              if temp_key_pair:
   996         2     376098.0 188049.0      0.1                  temp_key_pair.delete()
   997         3    1023402.0 341134.0      0.2          return AzureInstance(self.provider, vm)

Total time: 490.461 s
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
  1054         3          6.0      2.0      0.0          ins = (instance if isinstance(instance, AzureInstance) else
  1055                                                          self.get(instance))
  1056         3          3.0      1.0      0.0          if not instance:
  1057                                                       return
  1058                                           
  1059                                                   # Remove IPs first to avoid a network interface conflict
  1060                                                   # pylint:disable=protected-access
  1061         3     658259.0 219419.7      0.1          for public_ip_id in ins._public_ip_ids:
  1062                                                       ins.remove_floating_ip(public_ip_id)
  1063         3  232371164.0 77457054.7     47.4          self.provider.azure_client.deallocate_vm(ins.id)
  1064         3  124970163.0 41656721.0     25.5          self.provider.azure_client.delete_vm(ins.id)
  1065                                                   # pylint:disable=protected-access
  1066         6         54.0      9.0      0.0          for nic_id in ins._nic_ids:
  1067         3   36080517.0 12026839.0      7.4              self.provider.azure_client.delete_nic(nic_id)
  1068                                                   # pylint:disable=protected-access
  1069         3         21.0      7.0      0.0          for data_disk in ins._vm.storage_profile.data_disks:
  1070                                                       if data_disk.managed_disk:
  1071                                                           # pylint:disable=protected-access
  1072                                                           if ins._vm.tags.get('delete_on_terminate',
  1073                                                                               'False') == 'True':
  1074                                                               self.provider.azure_client. \
  1075                                                                   delete_disk(data_disk.managed_disk.id)
  1076                                                   # pylint:disable=protected-access
  1077         3          6.0      2.0      0.0          if ins._vm.storage_profile.os_disk.managed_disk:
  1078         3         28.0      9.3      0.0              self.provider.azure_client. \
  1079         3   96380595.0 32126865.0     19.7                  delete_disk(ins._vm.storage_profile.os_disk.managed_disk.id)

Total time: 165.88 s
Function: create at line 113

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   113                                               @cb_helpers.deprecated_alias(network_id='network')
   114                                               @dispatch(event="provider.security.vm_firewalls.create",
   115                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   116                                               @profile
   117                                               def create(self, label, network, description=None):
   118         2         31.0     15.5      0.0          AzureVMFirewall.assert_valid_resource_label(label)
   119         2        102.0     51.0      0.0          name = AzureVMFirewall._generate_name_from_label(label, "cb-fw")
   120         2          5.0      2.5      0.0          net = network.id if isinstance(network, Network) else network
   121         2         10.0      5.0      0.0          parameters = {"location": self.provider.region_name,
   122         2          2.0      1.0      0.0                        "tags": {'Label': label,
   123         2          2.0      1.0      0.0                                 'network_id': net}}
   124                                           
   125         2          1.0      0.5      0.0          if description:
   126         2          5.0      2.5      0.0              parameters['tags'].update(Description=description)
   127                                           
   128         2         10.0      5.0      0.0          fw = self.provider.azure_client.create_vm_firewall(name,
   129         2   10108748.0 5054374.0      6.1                                                             parameters)
   130                                           
   131                                                   # Add default rules to negate azure default rules.
   132                                                   # See: https://github.com/CloudVE/cloudbridge/issues/106
   133                                                   # pylint:disable=protected-access
   134        14         40.0      2.9      0.0          for rule in fw.default_security_rules:
   135        12         17.0      1.4      0.0              rule_name = "cb-override-" + rule.name
   136                                                       # Transpose rules to priority 4001 onwards, because
   137                                                       # only 0-4096 are allowed for custom rules
   138        12         19.0      1.6      0.0              rule.priority = rule.priority - 61440
   139        12         11.0      0.9      0.0              rule.access = "Deny"
   140        12        108.0      9.0      0.0              self.provider.azure_client.create_vm_firewall_rule(
   141        12  132700240.0 11058353.3     80.0                  fw.id, rule_name, rule)
   142                                           
   143                                                   # Add a new custom rule allowing all outbound traffic to the internet
   144         2          3.0      1.5      0.0          parameters = {"priority": 3000,
   145         2          2.0      1.0      0.0                        "protocol": "*",
   146         2          1.0      0.5      0.0                        "source_port_range": "*",
   147         2          2.0      1.0      0.0                        "source_address_prefix": "*",
   148         2          2.0      1.0      0.0                        "destination_port_range": "*",
   149         2          3.0      1.5      0.0                        "destination_address_prefix": "Internet",
   150         2          2.0      1.0      0.0                        "access": "Allow",
   151         2         10.0      5.0      0.0                        "direction": "Outbound"}
   152         2         20.0     10.0      0.0          result = self.provider.azure_client.create_vm_firewall_rule(
   153         2   23070528.0 11535264.0     13.9              fw.id, "cb-default-internet-outbound", parameters)
   154         2          9.0      4.5      0.0          fw.security_rules.append(result)
   155                                           
   156         2         53.0     26.5      0.0          cb_fw = AzureVMFirewall(self.provider, fw)
   157         2          2.0      1.0      0.0          return cb_fw

Total time: 96.5834 s
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
  1093        11        153.0     13.9      0.0          self.assert_valid_resource_label(value)
  1094         3          9.0      3.0      0.0          self._vm.tags.update(Label=value or "")
  1095         3         22.0      7.3      0.0          self._provider.azure_client. \
  1096         3   96583183.0 32194394.3    100.0              update_vm_tags(self.id, self._vm)

Total time: 42.3776 s
Function: delete at line 1308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1308                                               @dispatch(event="provider.networking.subnets.delete",
  1309                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1310                                               @profile
  1311                                               def delete(self, subnet):
  1312         1          2.0      2.0      0.0          sn = subnet if isinstance(subnet, AzureSubnet) else self.get(subnet)
  1313         1          1.0      1.0      0.0          if sn:
  1314         1   10703257.0 10703257.0     25.3              self.provider.azure_client.delete_subnet(sn.id)
  1315                                                       # Although Subnet doesn't support labels, we use the parent
  1316                                                       # Network's tags to track the subnet's labels, thus that
  1317                                                       # network-level tag must be deleted with the subnet
  1318         1         51.0     51.0      0.0              net_id = sn.network_id
  1319         1     331141.0 331141.0      0.8              az_network = self.provider.azure_client.get_network(net_id)
  1320         1         10.0     10.0      0.0              az_network.tags.pop(sn.tag_name)
  1321         1          6.0      6.0      0.0              self.provider.azure_client.update_network_tags(
  1322         1   31343171.0 31343171.0     74.0                  az_network.id, az_network)

Total time: 35.753 s
Function: create at line 1283

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1283                                               @dispatch(event="provider.networking.subnets.create",
  1284                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1285                                               @profile
  1286                                               def create(self, label, network, cidr_block, zone):
  1287         1          9.0      9.0      0.0          AzureSubnet.assert_valid_resource_label(label)
  1288                                                   # Although Subnet doesn't support tags in Azure, we use the parent
  1289                                                   # Network's tags to track its subnets' labels
  1290         1         49.0     49.0      0.0          subnet_name = AzureSubnet._generate_name_from_label(label, "cb-sn")
  1291                                           
  1292                                                   network_id = network.id \
  1293         1          3.0      3.0      0.0              if isinstance(network, Network) else network
  1294                                           
  1295         1          6.0      6.0      0.0          subnet_info = self.provider.azure_client\
  1296                                                       .create_subnet(
  1297         1          1.0      1.0      0.0                  network_id,
  1298         1          1.0      1.0      0.0                  subnet_name,
  1299                                                           {
  1300         1    3961283.0 3961283.0     11.1                      'address_prefix': cidr_block
  1301                                                           }
  1302                                                       )
  1303                                           
  1304         1         19.0     19.0      0.0          subnet = AzureSubnet(self.provider, subnet_info)
  1305         1   31791675.0 31791675.0     88.9          subnet.label = label
  1306         1          1.0      1.0      0.0          return subnet

Total time: 34.0238 s
Function: delete at line 461

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   461                                               @dispatch(event="provider.storage.volumes.delete",
   462                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   463                                               @profile
   464                                               def delete(self, volume_id):
   465         1          5.0      5.0      0.0          vol_id = (volume_id.id if isinstance(volume_id, AzureVolume)
   466                                                             else volume_id)
   467         1   34023747.0 34023747.0    100.0          self.provider.azure_client.delete_disk(vol_id)

Total time: 32.9634 s
Function: create at line 413

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   413                                               @dispatch(event="provider.storage.volumes.create",
   414                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   415                                               @profile
   416                                               def create(self, label, size, zone, snapshot=None, description=None):
   417         1         11.0     11.0      0.0          AzureVolume.assert_valid_resource_label(label)
   418         1         37.0     37.0      0.0          disk_name = AzureVolume._generate_name_from_label(label, "cb-vol")
   419         1          2.0      2.0      0.0          tags = {'Label': label}
   420                                           
   421         1          2.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   422                                                   snapshot = (self.provider.storage.snapshots.get(snapshot)
   423         1          0.0      0.0      0.0                      if snapshot and isinstance(snapshot, str) else snapshot)
   424                                           
   425         1          1.0      1.0      0.0          if description:
   426                                                       tags.update(Description=description)
   427                                           
   428         1          1.0      1.0      0.0          if snapshot:
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
   445         1          1.0      1.0      0.0                      zone_id or self.provider.region_name,
   446         1          1.0      1.0      0.0                  'disk_size_gb': size,
   447                                                           'creation_data': {
   448         1          2.0      2.0      0.0                      'create_option': DiskCreateOption.empty
   449                                                           },
   450         1          1.0      1.0      0.0                  'tags': tags
   451                                                       }
   452                                           
   453         1     524645.0 524645.0      1.6              disk = self.provider.azure_client.create_empty_disk(disk_name,
   454         1   32240191.0 32240191.0     97.8                                                                  params)
   455                                           
   456         1     198406.0 198406.0      0.6          azure_vol = self.provider.azure_client.get_disk(disk.id)
   457         1         61.0     61.0      0.0          cb_vol = AzureVolume(self.provider, azure_vol)
   458                                           
   459         1          1.0      1.0      0.0          return cb_vol

Total time: 31.7917 s
Function: label at line 957

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   957                                               @label.setter
   958                                               # pylint:disable=arguments-differ
   959                                               @profile
   960                                               def label(self, value):
   961         1          9.0      9.0      0.0          self.assert_valid_resource_label(value)
   962         1     279318.0 279318.0      0.9          network = self.network
   963                                                   # pylint:disable=protected-access
   964         1          0.0      0.0      0.0          az_network = network._network
   965         1          7.0      7.0      0.0          kwargs = {self.tag_name: value or ""}
   966         1          2.0      2.0      0.0          az_network.tags.update(**kwargs)
   967         1          6.0      6.0      0.0          self._provider.azure_client.update_network_tags(
   968         1   31512310.0 31512310.0     99.1              az_network.id, az_network)

Total time: 25.2464 s
Function: delete at line 159

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   159                                               @dispatch(event="provider.security.vm_firewalls.delete",
   160                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   161                                               @profile
   162                                               def delete(self, vm_firewall):
   163         2         12.0      6.0      0.0          fw_id = (vm_firewall.id if isinstance(vm_firewall, AzureVMFirewall)
   164                                                            else vm_firewall)
   165         2   25246418.0 12623209.0    100.0          self.provider.azure_client.delete_vm_firewall(fw_id)

Total time: 11.6034 s
Function: create at line 1369

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1369                                               @dispatch(event="provider.networking.routers.create",
  1370                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1371                                               @profile
  1372                                               def create(self, label, network):
  1373         1         60.0     60.0      0.0          router_name = AzureRouter._generate_name_from_label(label, "cb-router")
  1374                                           
  1375         1          6.0      6.0      0.0          parameters = {"location": self.provider.region_name,
  1376         1          2.0      2.0      0.0                        "tags": {'Label': label}}
  1377                                           
  1378         1         14.0     14.0      0.0          route = self.provider.azure_client. \
  1379         1   11603289.0 11603289.0    100.0              create_route_table(router_name, parameters)
  1380         1         19.0     19.0      0.0          return AzureRouter(self.provider, route)

Total time: 10.7982 s
Function: delete at line 1382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1382                                               @dispatch(event="provider.networking.routers.delete",
  1383                                                         priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
  1384                                               @profile
  1385                                               def delete(self, router):
  1386         1          3.0      3.0      0.0          r = router if isinstance(router, AzureRouter) else self.get(router)
  1387         1          1.0      1.0      0.0          if r:
  1388         1   10798151.0 10798151.0    100.0              self.provider.azure_client.delete_route_table(r.name)

Total time: 10.7652 s
Function: delete at line 1468

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1468                                               @dispatch(event="provider.networking.floating_ips.delete",
  1469                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1470                                               @profile
  1471                                               def delete(self, gateway, fip):
  1472         1          3.0      3.0      0.0          fip_id = fip.id if isinstance(fip, AzureFloatingIP) else fip
  1473         1   10765237.0 10765237.0    100.0          self.provider.azure_client.delete_floating_ip(fip_id)

Total time: 7.94915 s
Function: create at line 306

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   306                                               @dispatch(event="provider.security.key_pairs.create",
   307                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   308                                               @profile
   309                                               def create(self, name, public_key_material=None):
   310         3         28.0      9.3      0.0          AzureKeyPair.assert_valid_resource_name(name)
   311         3    6710353.0 2236784.3     84.4          key_pair = self.get(name)
   312                                           
   313         3          3.0      1.0      0.0          if key_pair:
   314                                                       raise DuplicateResourceException(
   315                                                           'Keypair already exists with name {0}'.format(name))
   316                                           
   317         3          2.0      0.7      0.0          private_key = None
   318         3          3.0      1.0      0.0          if not public_key_material:
   319         3     183927.0  61309.0      2.3              public_key_material, private_key = cb_helpers.generate_key_pair()
   320                                           
   321                                                   entity = {
   322         3          8.0      2.7      0.0              'PartitionKey': AzureKeyPairService.PARTITION_KEY,
   323         3        103.0     34.3      0.0              'RowKey': str(uuid.uuid4()),
   324         3          3.0      1.0      0.0              'Name': name,
   325         3          2.0      0.7      0.0              'Key': public_key_material
   326                                                   }
   327                                           
   328         3     387851.0 129283.7      4.9          self.provider.azure_client.create_public_key(entity)
   329         3     666858.0 222286.0      8.4          key_pair = self.get(name)
   330         3          7.0      2.3      0.0          key_pair.material = private_key
   331         3          2.0      0.7      0.0          return key_pair

Total time: 7.34557 s
Function: get at line 259

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   259                                               @dispatch(event="provider.security.key_pairs.get",
   260                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   261                                               @profile
   262                                               def get(self, key_pair_id):
   263         6          6.0      1.0      0.0          try:
   264         6         47.0      7.8      0.0              key_pair = self.provider.azure_client.\
   265         6    7345454.0 1224242.3    100.0                  get_public_key(key_pair_id)
   266                                           
   267         6         11.0      1.8      0.0              if key_pair:
   268         3         50.0     16.7      0.0                  return AzureKeyPair(self.provider, key_pair)
   269         3          2.0      0.7      0.0              return None
   270                                                   except AzureException as error:
   271                                                       log.debug("KeyPair %s was not found.", key_pair_id)
   272                                                       log.debug(error)
   273                                                       return None

Total time: 6.71618 s
Function: refresh at line 1340

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1340                                               @profile
  1341                                               def refresh(self):
  1342                                                   """
  1343                                                   Refreshes the state of this instance by re-querying the cloud provider
  1344                                                   for its latest state.
  1345                                                   """
  1346        17         35.0      2.1      0.0          try:
  1347        17    6715501.0 395029.5    100.0              self._vm = self._provider.azure_client.get_vm(self.id)
  1348        13         28.0      2.2      0.0              if not self._vm.tags:
  1349                                                           self._vm.tags = {}
  1350        13         75.0      5.8      0.0              self._update_state()
  1351         4         12.0      3.0      0.0          except (CloudError, ValueError) as cloud_error:
  1352         4        517.0    129.2      0.0              log.exception(cloud_error.message)
  1353                                                       # The volume no longer exists and cannot be refreshed.
  1354                                                       # set the state to unknown
  1355         4          8.0      2.0      0.0              self._state = 'unknown'

Total time: 5.08459 s
Function: create at line 1452

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1452                                               @dispatch(event="provider.networking.floating_ips.create",
  1453                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1454                                               @profile
  1455                                               def create(self, gateway):
  1456                                                   public_ip_parameters = {
  1457         1          9.0      9.0      0.0              'location': self.provider.azure_client.region_name,
  1458         1          1.0      1.0      0.0              'public_ip_allocation_method': 'Static'
  1459                                                   }
  1460                                           
  1461         1          2.0      2.0      0.0          public_ip_name = AzureFloatingIP._generate_name_from_label(
  1462         1         47.0     47.0      0.0              None, 'cb-fip-')
  1463                                           
  1464         1          4.0      4.0      0.0          floating_ip = self.provider.azure_client.\
  1465         1    5084513.0 5084513.0    100.0              create_floating_ip(public_ip_name, public_ip_parameters)
  1466         1         18.0     18.0      0.0          return AzureFloatingIP(self.provider, floating_ip)

Total time: 4.99243 s
Function: create at line 1189

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1189                                               @dispatch(event="provider.networking.networks.create",
  1190                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1191                                               @profile
  1192                                               def create(self, label, cidr_block):
  1193         1         10.0     10.0      0.0          AzureNetwork.assert_valid_resource_label(label)
  1194                                                   params = {
  1195         1     339834.0 339834.0      6.8              'location': self.provider.azure_client.region_name,
  1196                                                       'address_space': {
  1197         1          2.0      2.0      0.0                  'address_prefixes': [cidr_block]
  1198                                                       },
  1199         1          1.0      1.0      0.0              'tags': {'Label': label}
  1200                                                   }
  1201                                           
  1202         1         61.0     61.0      0.0          network_name = AzureNetwork._generate_name_from_label(label, 'cb-net')
  1203                                           
  1204         1         10.0     10.0      0.0          az_network = self.provider.azure_client.create_network(network_name,
  1205         1    4652478.0 4652478.0     93.2                                                                 params)
  1206         1         37.0     37.0      0.0          cb_network = AzureNetwork(self.provider, az_network)
  1207         1          1.0      1.0      0.0          return cb_network

Total time: 4.71943 s
Function: list at line 1095

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1095                                               @dispatch(event="provider.compute.vm_types.list",
  1096                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
  1097                                               @profile
  1098                                               def list(self, limit=None, marker=None):
  1099         5          9.0      1.8      0.0          vm_types = [AzureVMType(self.provider, vm_type)
  1100         5    4719066.0 943813.2    100.0                      for vm_type in self.instance_data]
  1101         5         44.0      8.8      0.0          return ClientPagedResultList(self.provider, vm_types,
  1102         5        314.0     62.8      0.0                                       limit=limit, marker=marker)

Total time: 4.52462 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         4          4.0      1.0      0.0          obj_list = self
   230         4          3.0      0.8      0.0          filters = ['name']
   231         4    4524522.0 1131130.5    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         4         90.0     22.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 3.44313 s
Function: get_or_create_default at line 320

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   320                                               @profile
   321                                               def get_or_create_default(self, zone):
   322                                                   # Look for a CB-default subnet
   323         2    3443125.0 1721562.5    100.0          matches = self.find(label=BaseSubnet.CB_DEFAULT_SUBNET_LABEL)
   324         2          2.0      1.0      0.0          if matches:
   325         2          3.0      1.5      0.0              return matches[0]
   326                                           
   327                                                   # No provider-default Subnet exists, try to create it (net + subnets)
   328                                                   network = self.provider.networking.networks.get_or_create_default()
   329                                                   subnet = self.create(BaseSubnet.CB_DEFAULT_SUBNET_LABEL, network,
   330                                                                        BaseSubnet.CB_DEFAULT_SUBNET_IPV4RANGE, zone)
   331                                                   return subnet

Total time: 3.42406 s
Function: find at line 1272

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1272                                               @dispatch(event="provider.networking.subnets.find",
  1273                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1274                                               @profile
  1275                                               def find(self, network=None, **kwargs):
  1276         2    2109626.0 1054813.0     61.6          obj_list = self._list_subnets(network)
  1277         2          4.0      2.0      0.0          filters = ['label']
  1278         2    1314359.0 657179.5     38.4          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1279                                           
  1280         2          6.0      3.0      0.0          return ClientPagedResultList(self.provider,
  1281         2         64.0     32.0      0.0                                       matches if matches else [])

Total time: 2.6431 s
Function: get at line 1168

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1168                                               @dispatch(event="provider.networking.networks.get",
  1169                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1170                                               @profile
  1171                                               def get(self, network_id):
  1172         9         11.0      1.2      0.0          try:
  1173         9    2642843.0 293649.2    100.0              network = self.provider.azure_client.get_network(network_id)
  1174         9        251.0     27.9      0.0              return AzureNetwork(self.provider, network)
  1175                                                   except (CloudError, InvalidValueException) as cloud_error:
  1176                                                       # Azure raises the cloud error if the resource not available
  1177                                                       log.exception(cloud_error)
  1178                                                       return None

Total time: 2.64084 s
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
  1006         5          7.0      1.4      0.0          instances = [AzureInstance(self.provider, inst)
  1007         5    2640620.0 528124.0    100.0                       for inst in self.provider.azure_client.list_vm()]
  1008         5         26.0      5.2      0.0          return ClientPagedResultList(self.provider, instances,
  1009         5        182.0     36.4      0.0                                       limit=limit, marker=marker)

Total time: 1.56939 s
Function: list at line 1180

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1180                                               @dispatch(event="provider.networking.networks.list",
  1181                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1182                                               @profile
  1183                                               def list(self, limit=None, marker=None):
  1184         2         31.0     15.5      0.0          networks = [AzureNetwork(self.provider, network)
  1185         2    1569280.0 784640.0    100.0                      for network in self.provider.azure_client.list_networks()]
  1186         2          6.0      3.0      0.0          return ClientPagedResultList(self.provider, networks,
  1187         2         70.0     35.0      0.0                                       limit=limit, marker=marker)

Total time: 1.03678 s
Function: find at line 1027

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1027                                               @dispatch(event="provider.compute.instances.find",
  1028                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
  1029                                               @profile
  1030                                               def find(self, **kwargs):
  1031         3          3.0      1.0      0.0          obj_list = self
  1032         3          3.0      1.0      0.0          filters = ['label']
  1033         3    1036722.0 345574.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
  1034                                           
  1035                                                   # All kwargs should have been popped at this time.
  1036         2          3.0      1.5      0.0          if len(kwargs) > 0:
  1037                                                       raise InvalidParamException(
  1038                                                           "Unrecognised parameters for search: %s. Supported "
  1039                                                           "attributes: %s" % (kwargs, ", ".join(filters)))
  1040                                           
  1041         2          4.0      2.0      0.0          return ClientPagedResultList(self.provider,
  1042         2         46.0     23.0      0.0                                       matches if matches else [])

Total time: 0.961534 s
Function: get at line 93

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
    93                                               @dispatch(event="provider.security.vm_firewalls.get",
    94                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    95                                               @profile
    96                                               def get(self, vm_firewall_id):
    97         4          7.0      1.8      0.0          try:
    98         4     961436.0 240359.0    100.0              fws = self.provider.azure_client.get_vm_firewall(vm_firewall_id)
    99         4         91.0     22.8      0.0              return AzureVMFirewall(self.provider, fws)
   100                                                   except (CloudError, InvalidValueException) as cloud_error:
   101                                                       # Azure raises the cloud error if the resource not available
   102                                                       log.exception(cloud_error)
   103                                                       return None

Total time: 0.768687 s
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
  1019         3          2.0      0.7      0.0          try:
  1020         3     768308.0 256102.7    100.0              vm = self.provider.azure_client.get_vm(instance_id)
  1021         1         18.0     18.0      0.0              return AzureInstance(self.provider, vm)
  1022         2          7.0      3.5      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1023                                                       # Azure raises the cloud error if the resource not available
  1024         2        349.0    174.5      0.0              log.exception(cloud_error)
  1025         2          3.0      1.5      0.0              return None

Total time: 0.703833 s
Function: delete at line 333

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   333                                               @dispatch(event="provider.security.key_pairs.delete",
   334                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   335                                               @profile
   336                                               def delete(self, key_pair):
   337         3          9.0      3.0      0.0          key_pair = (key_pair if isinstance(key_pair, AzureKeyPair) else
   338                                                               self.get(key_pair))
   339         3          4.0      1.3      0.0          if key_pair:
   340                                                       # pylint:disable=protected-access
   341         3     703820.0 234606.7    100.0              self.provider.azure_client.delete_public_key(key_pair._key_pair)

Total time: 0.618865 s
Function: get at line 1109

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1109                                               @dispatch(event="provider.compute.regions.get",
  1110                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
  1111                                               @profile
  1112                                               def get(self, region_id):
  1113         4          4.0      1.0      0.0          region = None
  1114        12     618660.0  51555.0    100.0          for azureRegion in self.provider.azure_client.list_locations():
  1115        12         14.0      1.2      0.0              if azureRegion.name == region_id:
  1116         4         63.0     15.8      0.0                  region = AzureRegion(self.provider, azureRegion)
  1117         4        122.0     30.5      0.0                  break
  1118         4          2.0      0.5      0.0          return region

Total time: 0.594712 s
Function: create at line 512

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   512                                               @dispatch(event="provider.storage.snapshots.create",
   513                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   514                                               @profile
   515                                               def create(self, label, volume, description=None):
   516         1         20.0     20.0      0.0          AzureSnapshot.assert_valid_resource_label(label)
   517         1          2.0      2.0      0.0          snapshot_name = AzureSnapshot._generate_name_from_label(label,
   518         1         51.0     51.0      0.0                                                                  "cb-snap")
   519         1          1.0      1.0      0.0          tags = {'Label': label}
   520         1          1.0      1.0      0.0          if description:
   521         1          4.0      4.0      0.0              tags.update(Description=description)
   522                                           
   523                                                   volume = (self.provider.storage.volumes.get(volume)
   524         1          3.0      3.0      0.0                    if isinstance(volume, str) else volume)
   525                                           
   526                                                   params = {
   527         1         11.0     11.0      0.0              'location': self.provider.azure_client.region_name,
   528                                                       'creation_data': {
   529         1          3.0      3.0      0.0                  'create_option': DiskCreateOption.copy,
   530         1          8.0      8.0      0.0                  'source_uri': volume.resource_id
   531                                                       },
   532         1          1.0      1.0      0.0              'disk_size_gb': volume.size,
   533         1          1.0      1.0      0.0              'tags': tags
   534                                                   }
   535                                           
   536         1          3.0      3.0      0.0          azure_snap = self.provider.azure_client.create_snapshot(snapshot_name,
   537         1     594603.0 594603.0    100.0                                                                  params)
   538                                                   return AzureSnapshot(self.provider, azure_snap)

Total time: 0.57252 s
Function: refresh at line 1474

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1474                                               @profile
  1475                                               def refresh(self):
  1476         2         21.0     10.5      0.0          self._route_table = self._provider.azure_client. \
  1477         2     572499.0 286249.5    100.0              get_route_table(self._route_table.name)

Total time: 0.53395 s
Function: refresh at line 852

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   852                                               @profile
   853                                               def refresh(self):
   854                                                   # Gateway is not needed as it doesn't exist in Azure, so just
   855                                                   # getting the Floating IP again from the client
   856                                                   # pylint:disable=protected-access
   857         2     533944.0 266972.0    100.0          fip = self._provider.networking._floating_ips.get(None, self.id)
   858                                                   # pylint:disable=protected-access
   859         2          6.0      3.0      0.0          self._ip = fip._ip

Total time: 0.522689 s
Function: get at line 1430

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1430                                               @dispatch(event="provider.networking.floating_ips.get",
  1431                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1432                                               @profile
  1433                                               def get(self, gateway, fip_id):
  1434         2          2.0      1.0      0.0          try:
  1435         2     522540.0 261270.0    100.0              az_ip = self.provider.azure_client.get_floating_ip(fip_id)
  1436         1          3.0      3.0      0.0          except (CloudError, InvalidValueException) as cloud_error:
  1437                                                       # Azure raises the cloud error if the resource not available
  1438         1        130.0    130.0      0.0              log.exception(cloud_error)
  1439         1          1.0      1.0      0.0              return None
  1440         1         13.0     13.0      0.0          return AzureFloatingIP(self.provider, az_ip)

Total time: 0.378508 s
Function: get at line 677

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   677                                               @profile
   678                                               def get(self, image_id):
   679                                                   """
   680                                                   Returns an Image given its id
   681                                                   """
   682         4          2.0      0.5      0.0          try:
   683         4     378438.0  94609.5    100.0              image = self.provider.azure_client.get_image(image_id)
   684         4         68.0     17.0      0.0              return AzureMachineImage(self.provider, image)
   685                                                   except (CloudError, InvalidValueException) as cloud_error:
   686                                                       # Azure raises the cloud error if the resource not available
   687                                                       log.exception(cloud_error)
   688                                                       return None

Total time: 0.325217 s
Function: refresh at line 782

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   782                                               @profile
   783                                               def refresh(self):
   784                                                   """
   785                                                   Refreshes the state of this network by re-querying the cloud provider
   786                                                   for its latest state.
   787                                                   """
   788         1          3.0      3.0      0.0          try:
   789         1         10.0     10.0      0.0              self._network = self._provider.azure_client.\
   790         1     325080.0 325080.0    100.0                  get_network(self.id)
   791                                                       self._state = self._network.provisioning_state
   792         1          2.0      2.0      0.0          except (CloudError, ValueError) as cloud_error:
   793         1        118.0    118.0      0.0              log.exception(cloud_error.message)
   794                                                       # The network no longer exists and cannot be refreshed.
   795                                                       # set the state to unknown
   796         1          4.0      4.0      0.0              self._state = 'unknown'

Total time: 0.251713 s
Function: refresh at line 999

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   999                                               @profile
  1000                                               def refresh(self):
  1001                                                   """
  1002                                                   Refreshes the state of this network by re-querying the cloud provider
  1003                                                   for its latest state.
  1004                                                   """
  1005         1          5.0      5.0      0.0          try:
  1006         1         14.0     14.0      0.0              self._subnet = self._provider.azure_client. \
  1007         1     251559.0 251559.0     99.9                  get_subnet(self.id)
  1008                                                       self._state = self._subnet.provisioning_state
  1009         1          3.0      3.0      0.0          except (CloudError, ValueError) as cloud_error:
  1010         1        130.0    130.0      0.1              log.exception(cloud_error.message)
  1011                                                       # The subnet no longer exists and cannot be refreshed.
  1012                                                       # set the state to unknown
  1013         1          2.0      2.0      0.0              self._state = 'unknown'

Total time: 0.231875 s
Function: get at line 218

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   218                                               @dispatch(event="provider.compute.vm_types.get",
   219                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   220                                               @profile
   221                                               def get(self, vm_type_id):
   222         1          5.0      5.0      0.0          vm_type = (t for t in self if t.id == vm_type_id)
   223         1     231870.0 231870.0    100.0          return next(vm_type, None)

Total time: 0.199181 s
Function: list at line 1264

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1264                                               @dispatch(event="provider.networking.subnets.list",
  1265                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1266                                               @profile
  1267                                               def list(self, network=None, limit=None, marker=None):
  1268         1          7.0      7.0      0.0          return ClientPagedResultList(self.provider,
  1269         1     199134.0 199134.0    100.0                                       self._list_subnets(network),
  1270         1         40.0     40.0      0.0                                       limit=limit, marker=marker)

Total time: 0.000324 s
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
   181         4          5.0      1.2      1.5          rules = [AzureVMFirewallRule(firewall, rule) for rule
   182         4        196.0     49.0     60.5                   in firewall._vm_firewall.security_rules
   183                                                            if rule.priority < 3500]
   184         4         11.0      2.8      3.4          return ClientPagedResultList(self.provider, rules,
   185         4        112.0     28.0     34.6                                       limit=limit, marker=marker)

Total time: 3.6e-05 s
Function: get_or_create at line 1403

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1403                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1404                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1405                                               @profile
  1406                                               def get_or_create(self, network):
  1407         1         36.0     36.0    100.0          return self._gateway_singleton(network)

Total time: 1.7e-05 s
Function: create_launch_config at line 859

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   859                                               @profile
   860                                               def create_launch_config(self):
   861         1         17.0     17.0    100.0          return AzureLaunchConfig(self.provider)

