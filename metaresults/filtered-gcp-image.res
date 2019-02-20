cloudbridge.test.test_image_service.CloudImageServiceTestCase


Test output
 ..
----------------------------------------------------------------------
Ran 2 tests in 696.940s

OK

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 170.308 s
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
   653       223  170303125.0 763691.1    100.0          instance = self.provider.get_resource('instances', instance_id)
   654       223       4754.0     21.3      0.0          return GCPInstance(self.provider, instance) if instance else None

Total time: 169.705 s
Function: refresh at line 1237

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1237                                               @profile
  1238                                               def refresh(self):
  1239                                                   """
  1240                                                   Refreshes the state of this instance by re-querying the cloud provider
  1241                                                   for its latest state.
  1242                                                   """
  1243       221  169702381.0 767884.1    100.0          inst = self._provider.compute.instances.get(self.id)
  1244       221        280.0      1.3      0.0          if inst:
  1245                                                       # pylint:disable=protected-access
  1246       219       1973.0      9.0      0.0              self._gcp_instance = inst._gcp_instance
  1247                                                   else:
  1248                                                       # instance no longer exists
  1249         2          6.0      3.0      0.0              self._gcp_instance['status'] = InstanceState.UNKNOWN

Total time: 101.152 s
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
   499         2         23.0     11.5      0.0          GCPInstance.assert_valid_resource_name(label)
   500         2          9.0      4.5      0.0          zone_name = self.provider.default_zone
   501         2          4.0      2.0      0.0          if zone:
   502         2          6.0      3.0      0.0              if not isinstance(zone, GCPPlacementZone):
   503         2          4.0      2.0      0.0                  zone = GCPPlacementZone(
   504         2          5.0      2.5      0.0                      self.provider,
   505         2     311408.0 155704.0      0.3                      self.provider.get_resource('zones', zone))
   506         2         25.0     12.5      0.0              zone_name = zone.name
   507         2         11.0      5.5      0.0          if not isinstance(vm_type, GCPVMType):
   508         2     321874.0 160937.0      0.3              vm_type = self.provider.compute.vm_types.get(vm_type)
   509                                           
   510         2          6.0      3.0      0.0          network_interface = {'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
   511         2          8.0      4.0      0.0                                                  'name': 'External NAT'}]}
   512         2          7.0      3.5      0.0          if subnet:
   513         2         11.0      5.5      0.0              network_interface['subnetwork'] = subnet.id
   514                                                   else:
   515                                                       network_interface['network'] = 'global/networks/default'
   516                                           
   517         2          6.0      3.0      0.0          num_roots = 0
   518         2          5.0      2.5      0.0          disks = []
   519         2          6.0      3.0      0.0          boot_disk = None
   520         2          9.0      4.5      0.0          if isinstance(launch_config, GCPLaunchConfig):
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
   562         2          7.0      3.5      0.0          if num_roots > 1:
   563                                                       log.warning('The launch config contains %d boot disks. Will '
   564                                                                   'use the first one', num_roots)
   565         2          6.0      3.0      0.0          if image:
   566         2          6.0      3.0      0.0              if boot_disk:
   567                                                           log.warning('A boot image is given while the launch config '
   568                                                                       'contains a boot disk, too. The launch config '
   569                                                                       'will be used.')
   570                                                       else:
   571         2          7.0      3.5      0.0                  if not isinstance(image, GCPMachineImage):
   572         1     186959.0 186959.0      0.2                      image = self.provider.compute.images.get(image)
   573                                                           # Explicitly set diskName; otherwise, instance name will be
   574                                                           # used by default which may conflict with existing disks.
   575                                                           boot_disk = {
   576         2          6.0      3.0      0.0                      'boot': True,
   577         2          6.0      3.0      0.0                      'autoDelete': True,
   578                                                               'initializeParams': {
   579         2         13.0      6.5      0.0                          'sourceImage': image.id,
   580         2        144.0     72.0      0.0                          'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}
   581                                           
   582         2          7.0      3.5      0.0          if not boot_disk:
   583                                                       log.warning('No boot disk is given for instance %s.', label)
   584                                                       return None
   585                                                   # The boot disk must be the first disk attached to the instance.
   586         2         10.0      5.0      0.0          disks.insert(0, boot_disk)
   587                                           
   588                                                   config = {
   589         2        112.0     56.0      0.0              'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
   590         2         11.0      5.5      0.0              'machineType': vm_type.resource_url,
   591         2          6.0      3.0      0.0              'disks': disks,
   592         2          8.0      4.0      0.0              'networkInterfaces': [network_interface]
   593                                                   }
   594                                           
   595         2          5.0      2.5      0.0          if vm_firewalls and isinstance(vm_firewalls, list):
   596                                                       vm_firewall_names = []
   597                                                       if isinstance(vm_firewalls[0], VMFirewall):
   598                                                           vm_firewall_names = [f.name for f in vm_firewalls]
   599                                                       elif isinstance(vm_firewalls[0], str):
   600                                                           vm_firewall_names = vm_firewalls
   601                                                       if len(vm_firewall_names) > 0:
   602                                                           config['tags'] = {}
   603                                                           config['tags']['items'] = vm_firewall_names
   604                                           
   605         2          5.0      2.5      0.0          if user_data:
   606                                                       entry = {'key': 'user-data', 'value': user_data}
   607                                                       config['metadata'] = {'items': [entry]}
   608                                           
   609         2          6.0      3.0      0.0          if key_pair:
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
   629         2          7.0      3.5      0.0          config['labels'] = {'cblabel': label}
   630                                           
   631         2      51129.0  25564.5      0.1          operation = (self.provider
   632                                                                    .gcp_compute.instances()
   633         2          6.0      3.0      0.0                           .insert(project=self.provider.project_name,
   634         2          2.0      1.0      0.0                                   zone=zone_name,
   635         2    3323984.0 1661992.0      3.3                                   body=config)
   636                                                                    .execute())
   637         2         10.0      5.0      0.0          instance_id = operation.get('targetLink')
   638         2   96292576.0 48146288.0     95.2          self.provider.wait_for_operation(operation, zone=zone_name)
   639         2     663453.0 331726.5      0.7          cb_inst = self.get(instance_id)
   640         2          8.0      4.0      0.0          return cb_inst

Total time: 41.9159 s
Function: list at line 467

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   467                                               @profile
   468                                               def list(self, limit=None, marker=None):
   469                                                   """
   470                                                   List all images.
   471                                                   """
   472       221    1442223.0   6525.9      3.4          self._retrieve_public_images()
   473       221        230.0      1.0      0.0          images = []
   474       221        489.0      2.2      0.0          if (self.provider.project_name not in
   475       221        423.0      1.9      0.0                  GCPImageService._PUBLIC_IMAGE_PROJECTS):
   476       221        342.0      1.5      0.0              for image in helpers.iter_all(
   477       221    1629065.0   7371.3      3.9                      self.provider.gcp_compute.images(),
   478       441   38641821.0  87623.2     92.2                      project=self.provider.project_name):
   479       220       4479.0     20.4      0.0                  images.append(GCPMachineImage(self.provider, image))
   480       221       2253.0     10.2      0.0          images.extend(self._public_images)
   481       221        504.0      2.3      0.0          return ClientPagedResultList(self.provider, images,
   482       221     194065.0    878.1      0.5                                       limit=limit, marker=marker)

Total time: 5.04476 s
Function: list at line 1645

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1645                                               @dispatch(event="provider.networking.floating_ips.list",
  1646                                                         priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
  1647                                               @profile
  1648                                               def list(self, gateway, limit=None, marker=None):
  1649         3          5.0      1.7      0.0          max_result = limit if limit is not None and limit < 500 else 500
  1650         3      13040.0   4346.7      0.3          response = (self.provider
  1651                                                                   .gcp_compute
  1652                                                                   .addresses()
  1653         3          8.0      2.7      0.0                          .list(project=self.provider.project_name,
  1654         3          6.0      2.0      0.0                                region=self.provider.region_name,
  1655         3          3.0      1.0      0.0                                maxResults=max_result,
  1656         3    1564894.0 521631.3     31.0                                pageToken=marker)
  1657                                                                   .execute())
  1658         3         12.0      4.0      0.0          ips = [GCPFloatingIP(self.provider, ip)
  1659         3    3466730.0 1155576.7     68.7                 for ip in response.get('items', [])]
  1660         3         12.0      4.0      0.0          if len(ips) > max_result:
  1661                                                       log.warning('Expected at most %d results; got %d',
  1662                                                                   max_result, len(ips))
  1663         3          6.0      2.0      0.0          return ServerPagedResultList('nextPageToken' in response,
  1664         3          6.0      2.0      0.0                                       response.get('nextPageToken'),
  1665         3         37.0     12.3      0.0                                       False, data=ips)

Total time: 4.66685 s
Function: get at line 435

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   435                                               @profile
   436                                               def get(self, image_id):
   437                                                   """
   438                                                   Returns an Image given its id
   439                                                   """
   440        10    4658275.0 465827.5     99.8          image = self.provider.get_resource('images', image_id)
   441        10         24.0      2.4      0.0          if image:
   442         7        140.0     20.0      0.0              return GCPMachineImage(self.provider, image)
   443         3         11.0      3.7      0.0          self._retrieve_public_images()
   444      3237       1745.0      0.5      0.0          for public_image in self._public_images:
   445      3234       6650.0      2.1      0.1              if public_image.id == image_id or public_image.name == image_id:
   446                                                           return public_image
   447         3          1.0      0.3      0.0          return None

Total time: 4.07836 s
Function: refresh at line 761

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   761                                               @profile
   762                                               def refresh(self):
   763                                                   """
   764                                                   Refreshes the state of this instance by re-querying the cloud provider
   765                                                   for its latest state.
   766                                                   """
   767         7    4078322.0 582617.4    100.0          image = self._provider.compute.images.get(self.id)
   768         7          5.0      0.7      0.0          if image:
   769                                                       # pylint:disable=protected-access
   770         5         27.0      5.4      0.0              self._gcp_image = image._gcp_image
   771                                                   else:
   772                                                       # image no longer exists
   773         2          6.0      3.0      0.0              self._gcp_image['status'] = MachineImageState.UNKNOWN

Total time: 3.7366 s
Function: label at line 713

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   713                                               @label.setter
   714                                               # pylint:disable=arguments-differ
   715                                               @profile
   716                                               def label(self, value):
   717        11      69594.0   6326.7      1.9          req = (self._provider
   718                                                              .gcp_compute
   719                                                              .images()
   720        11         26.0      2.4      0.0                     .setLabels(project=self._provider.project_name,
   721        11         15.0      1.4      0.0                                resource=self.name,
   722        11       4744.0    431.3      0.1                                body={}))
   723                                           
   724        11    3662222.0 332929.3     98.0          helpers.change_label(self, 'cblabel', value, '_gcp_image', req)

Total time: 3.67662 s
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
  1108         1          4.0      4.0      0.0          region = self._zone_to_region(zone or self.provider.default_zone,
  1109         1     914587.0 914587.0     24.9                                        return_name_only=False)
  1110                                                   # Check if a default subnet already exists for the given region/zone
  1111         1    2762018.0 2762018.0     75.1          for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
  1112         1          7.0      7.0      0.0              if sn.region == region.id:
  1113         1          2.0      2.0      0.0                  return sn
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

Total time: 2.71797 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         1          2.0      2.0      0.0          if not network:
   313         1          1.0      1.0      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         1          1.0      1.0      0.0          filters = ['label']
   317         1    2717925.0 2717925.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         1         44.0     44.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 1.58702 s
Function: delete at line 704

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   704                                               @dispatch(event="provider.compute.instances.delete",
   705                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   706                                               @profile
   707                                               def delete(self, instance):
   708         2          5.0      2.5      0.0          instance = (instance if isinstance(instance, GCPInstance) else
   709                                                               self.get(instance))
   710         2          2.0      1.0      0.0          if instance:
   711         2      44160.0  22080.0      2.8              (self._provider
   712                                                        .gcp_compute
   713                                                        .instances()
   714         2          5.0      2.5      0.0               .delete(project=self.provider.project_name,
   715         2        789.0    394.5      0.0                       zone=instance.zone_name,
   716         2    1542062.0 771031.0     97.2                       instance=instance.name)
   717                                                        .execute())

Total time: 0.862251 s
Function: get at line 382

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   382                                               @dispatch(event="provider.compute.regions.get",
   383                                                         priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
   384                                               @profile
   385                                               def get(self, region_id):
   386         1          3.0      3.0      0.0          region = self.provider.get_resource('regions', region_id,
   387         1     862218.0 862218.0    100.0                                              region=region_id)
   388         1         30.0     30.0      0.0          return GCPRegion(self.provider, region) if region else None

Total time: 0.36834 s
Function: find at line 449

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   449                                               @profile
   450                                               def find(self, limit=None, marker=None, **kwargs):
   451                                                   """
   452                                                   Searches for an image by a given list of attributes
   453                                                   """
   454         3          5.0      1.7      0.0          label = kwargs.pop('label', None)
   455                                           
   456                                                   # All kwargs should have been popped at this time.
   457         3          6.0      2.0      0.0          if len(kwargs) > 0:
   458         1          1.0      1.0      0.0              raise InvalidParamException(
   459         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   460         1         15.0     15.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   461                                           
   462                                                   # Retrieve all available images by setting limit to sys.maxsize
   463         2     368244.0 184122.0    100.0          images = [image for image in self if image.label == label]
   464         2          7.0      3.5      0.0          return ClientPagedResultList(self.provider, images,
   465         2         61.0     30.5      0.0                                       limit=limit, marker=marker)

Total time: 0.30929 s
Function: get at line 341

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   341                                               @dispatch(event="provider.compute.vm_types.get",
   342                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   343                                               @profile
   344                                               def get(self, vm_type_id):
   345         2     309252.0 154626.0    100.0          vm_type = self.provider.get_resource('machineTypes', vm_type_id)
   346         2         38.0     19.0      0.0          return GCPVMType(self.provider, vm_type) if vm_type else None

Total time: 0.201059 s
Function: get at line 786

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   786                                               @dispatch(event="provider.networking.networks.get",
   787                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
   788                                               @profile
   789                                               def get(self, network_id):
   790         1     201018.0 201018.0    100.0          network = self.provider.get_resource('networks', network_id)
   791         1         41.0     41.0      0.0          return GCPNetwork(self.provider, network) if network else None

Total time: 0.186214 s
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
  1010         1          1.0      1.0      0.0          filter = None
  1011         1          1.0      1.0      0.0          if network is not None:
  1012                                                       network = (network if isinstance(network, GCPNetwork)
  1013                                                                  else self.provider.networking.networks.get(network))
  1014                                                       filter = 'network eq %s' % network.resource_url
  1015         1          1.0      1.0      0.0          if zone:
  1016                                                       region_name = self._zone_to_region(zone)
  1017                                                   else:
  1018         1          5.0      5.0      0.0              region_name = self.provider.region_name
  1019         1          1.0      1.0      0.0          subnets = []
  1020         1      10331.0  10331.0      5.5          response = (self.provider
  1021                                                                   .gcp_compute
  1022                                                                   .subnetworks()
  1023         1          3.0      3.0      0.0                          .list(project=self.provider.project_name,
  1024         1          1.0      1.0      0.0                                region=region_name,
  1025         1     175627.0 175627.0     94.3                                filter=filter)
  1026                                                                   .execute())
  1027         8         13.0      1.6      0.0          for subnet in response.get('items', []):
  1028         7         89.0     12.7      0.0              subnets.append(GCPSubnet(self.provider, subnet))
  1029         1          4.0      4.0      0.0          return ClientPagedResultList(self.provider, subnets,
  1030         1        137.0    137.0      0.1                                       limit=limit, marker=marker)

Total time: 2e-06 s
Function: get_or_create at line 1610

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1610                                               @dispatch(event="provider.networking.gateways.get_or_create",
  1611                                                         priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
  1612                                               @profile
  1613                                               def get_or_create(self, network):
  1614         1          2.0      2.0    100.0          return self._default_internet_gateway

