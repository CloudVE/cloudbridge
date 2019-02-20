cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase


Test output
 E....E
======================================================================
ERROR: test_attach_detach_volume (cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 45, in wrap_exception
    return next_handler.invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 110, in invoke
    result = self.callback(*args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/line_profiler.py", line 115, in wrapper
    result = func(*args, **kwds)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py", line 868, in create
    nics=nics)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/v2/servers.py", line 1327, in create
    return self._boot(response_key, *boot_args, **boot_kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/v2/servers.py", line 776, in _boot
    return_raw=return_raw, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/base.py", line 366, in _create
    resp, body = self.api.client.post(url, body=body)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/keystoneauth1/adapter.py", line 357, in post
    return self.request(url, 'POST', **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/client.py", line 83, in request
    raise exceptions.from_response(resp, body, url, method)
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-27dc45cc-5726-4dfc-a595-fd8927245175)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_block_store_service.py", line 77, in test_attach_detach_volume
    self.provider, label, subnet=subnet)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 207, in get_test_instance
    user_data=user_data)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 192, in create_test_instance
    user_data=user_data)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/middleware.py", line 74, in wrapper
    return dispatcher.dispatch(self, event, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 218, in dispatch
    return handlers[0].invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 78, in invoke
    result = self.callback(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 55, in wrap_exception
    six.raise_from(cb_ex, e)
  File "<string>", line 3, in raise_from
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-27dc45cc-5726-4dfc-a595-fd8927245175) from exception type: <class 'novaclient.exceptions.BadRequest'>

======================================================================
ERROR: test_volume_properties (cloudbridge.test.test_block_store_service.CloudBlockStoreServiceTestCase)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 45, in wrap_exception
    return next_handler.invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 110, in invoke
    result = self.callback(*args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/line_profiler.py", line 115, in wrapper
    result = func(*args, **kwds)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/providers/openstack/services.py", line 868, in create
    nics=nics)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/v2/servers.py", line 1327, in create
    return self._boot(response_key, *boot_args, **boot_kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/v2/servers.py", line 776, in _boot
    return_raw=return_raw, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/base.py", line 366, in _create
    resp, body = self.api.client.post(url, body=body)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/keystoneauth1/adapter.py", line 357, in post
    return self.request(url, 'POST', **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/novaclient/client.py", line 83, in request
    raise exceptions.from_response(resp, body, url, method)
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-9de03630-a3e6-47fe-99e8-46ec7310ec11)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_block_store_service.py", line 104, in test_volume_properties
    self.provider, label, subnet=subnet)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 207, in get_test_instance
    user_data=user_data)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 192, in create_test_instance
    user_data=user_data)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/middleware.py", line 74, in wrapper
    return dispatcher.dispatch(self, event, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 218, in dispatch
    return handlers[0].invoke(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/line/lib/python3.6/site-packages/pyeventsystem/events.py", line 78, in invoke
    result = self.callback(event_args, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/cloud/base/middleware.py", line 55, in wrap_exception
    six.raise_from(cb_ex, e)
  File "<string>", line 3, in raise_from
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-9de03630-a3e6-47fe-99e8-46ec7310ec11) from exception type: <class 'novaclient.exceptions.BadRequest'>

----------------------------------------------------------------------
Ran 6 tests in 107.915s

FAILED (errors=2)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 14.9996 s
Function: get at line 457

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   457                                               @dispatch(event="provider.storage.snapshots.get",
   458                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   459                                               @profile
   460                                               def get(self, snapshot_id):
   461        22         29.0      1.3      0.0          try:
   462        22         33.0      1.5      0.0              return OpenStackSnapshot(
   463        22         65.0      3.0      0.0                  self.provider,
   464        22   14999175.0 681780.7    100.0                  self.provider.cinder.volume_snapshots.get(snapshot_id))
   465         7         17.0      2.4      0.0          except CinderNotFound:
   466         7         55.0      7.9      0.0              log.debug("Snapshot %s was not found.", snapshot_id)
   467         7        204.0     29.1      0.0              return None

Total time: 12.7251 s
Function: refresh at line 748

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   748                                               @profile
   749                                               def refresh(self):
   750                                                   """
   751                                                   Refreshes the state of this snapshot by re-querying the cloud provider
   752                                                   for its latest state.
   753                                                   """
   754        18        287.0     15.9      0.0          snap = self._provider.storage.snapshots.get(
   755        18   12724661.0 706925.6    100.0              self.id)
   756        18         33.0      1.8      0.0          if snap:
   757                                                       # pylint:disable=protected-access
   758        13         61.0      4.7      0.0              self._snapshot = snap._snapshot
   759                                                   else:
   760                                                       # The snapshot no longer exists and cannot be refreshed.
   761                                                       # set the status to unknown
   762         5         11.0      2.2      0.0              self._snapshot.status = 'unknown'

Total time: 11.5862 s
Function: get at line 381

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   381                                               @dispatch(event="provider.storage.volumes.get",
   382                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   383                                               @profile
   384                                               def get(self, volume_id):
   385        16         19.0      1.2      0.0          try:
   386        16         21.0      1.3      0.0              return OpenStackVolume(
   387        16   11586041.0 724127.6    100.0                  self.provider, self.provider.cinder.volumes.get(volume_id))
   388         3          9.0      3.0      0.0          except CinderNotFound:
   389         3         41.0     13.7      0.0              log.debug("Volume %s was not found.", volume_id)
   390         3         95.0     31.7      0.0              return None

Total time: 10.4945 s
Function: create at line 787

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   787                                               @dispatch(event="provider.compute.instances.create",
   788                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   789                                               @profile
   790                                               def create(self, label, image, vm_type, subnet, zone,
   791                                                          key_pair=None, vm_firewalls=None, user_data=None,
   792                                                          launch_config=None, **kwargs):
   793         2         23.0     11.5      0.0          OpenStackInstance.assert_valid_resource_label(label)
   794         2          6.0      3.0      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   795                                                   vm_size = vm_type.id if \
   796         2          5.0      2.5      0.0              isinstance(vm_type, VMType) else \
   797         2         14.0      7.0      0.0              self.provider.compute.vm_types.find(
   798         2    6430674.0 3215337.0     61.3                  name=vm_type)[0].id
   799         2          7.0      3.5      0.0          if isinstance(subnet, Subnet):
   800         2         12.0      6.0      0.0              subnet_id = subnet.id
   801         2          9.0      4.5      0.0              net_id = subnet.network_id
   802                                                   else:
   803                                                       subnet_id = subnet
   804                                                       net_id = (self.provider.networking.subnets
   805                                                                 .get(subnet_id).network_id
   806                                                                 if subnet_id else None)
   807         2          6.0      3.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   808                                                   key_pair_name = key_pair.name if \
   809         2          6.0      3.0      0.0              isinstance(key_pair, KeyPair) else key_pair
   810         2          4.0      2.0      0.0          bdm = None
   811         2          5.0      2.5      0.0          if launch_config:
   812                                                       bdm = self._to_block_device_mapping(launch_config)
   813                                           
   814                                                   # Security groups must be passed in as a list of IDs and attached to a
   815                                                   # port if a port is being created. Otherwise, the security groups must
   816                                                   # be passed in as a list of names to the servers.create() call.
   817                                                   # OpenStack will respect the port's security groups first and then
   818                                                   # fall-back to the named security groups.
   819         2          6.0      3.0      0.0          sg_name_list = []
   820         2          4.0      2.0      0.0          nics = None
   821         2          5.0      2.5      0.0          if subnet_id:
   822         2          6.0      3.0      0.0              log.debug("Creating network port for %s in subnet: %s",
   823         2         18.0      9.0      0.0                        label, subnet_id)
   824         2          5.0      2.5      0.0              sg_list = []
   825         2          5.0      2.5      0.0              if vm_firewalls:
   826                                                           if isinstance(vm_firewalls, list) and \
   827                                                                   isinstance(vm_firewalls[0], VMFirewall):
   828                                                               sg_list = vm_firewalls
   829                                                           else:
   830                                                               sg_list = (self.provider.security.vm_firewalls
   831                                                                          .find(label=sg) for sg in vm_firewalls)
   832                                                               sg_list = (sg[0] for sg in sg_list if sg)
   833         2          8.0      4.0      0.0              sg_id_list = [sg.id for sg in sg_list]
   834                                                       port_def = {
   835         2          5.0      2.5      0.0                  "port": {
   836         2          4.0      2.0      0.0                      "admin_state_up": True,
   837         2          7.0      3.5      0.0                      "name": OpenStackInstance._generate_name_from_label(
   838         2        120.0     60.0      0.0                          label, 'cb-port'),
   839         2          5.0      2.5      0.0                      "network_id": net_id,
   840         2          6.0      3.0      0.0                      "fixed_ips": [{"subnet_id": subnet_id}],
   841         2          6.0      3.0      0.0                      "security_groups": sg_id_list
   842                                                           }
   843                                                       }
   844         2    2280250.0 1140125.0     21.7              port_id = self.provider.neutron.create_port(port_def)['port']['id']
   845         2         11.0      5.5      0.0              nics = [{'net-id': net_id, 'port-id': port_id}]
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
   856         2         26.0     13.0      0.0          log.debug("Launching in subnet %s", subnet_id)
   857         2         24.0     12.0      0.0          os_instance = self.provider.nova.servers.create(
   858         2          6.0      3.0      0.0              label,
   859         2         12.0      6.0      0.0              None if self._has_root_device(launch_config) else image_id,
   860         2          6.0      3.0      0.0              vm_size,
   861         2          6.0      3.0      0.0              min_count=1,
   862         2          7.0      3.5      0.0              max_count=1,
   863         2          6.0      3.0      0.0              availability_zone=zone_id,
   864         2          7.0      3.5      0.0              key_name=key_pair_name,
   865         2          6.0      3.0      0.0              security_groups=sg_name_list,
   866         2         10.0      5.0      0.0              userdata=str(user_data) or None,
   867         2          6.0      3.0      0.0              block_device_mapping_v2=bdm,
   868         2    1783138.0 891569.0     17.0              nics=nics)
   869                                                   return OpenStackInstance(self.provider, os_instance)

Total time: 9.45032 s
Function: refresh at line 662

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   662                                               @profile
   663                                               def refresh(self):
   664                                                   """
   665                                                   Refreshes the state of this volume by re-querying the cloud provider
   666                                                   for its latest state.
   667                                                   """
   668        14        220.0     15.7      0.0          vol = self._provider.storage.volumes.get(
   669        14    9450011.0 675000.8    100.0              self.id)
   670        14         24.0      1.7      0.0          if vol:
   671                                                       # pylint:disable=protected-access
   672        12         65.0      5.4      0.0              self._volume = vol._volume  # pylint:disable=protected-access
   673                                                   else:
   674                                                       # The volume no longer exists and cannot be refreshed.
   675                                                       # set the status to unknown
   676         2          4.0      2.0      0.0              self._volume.status = 'unknown'

Total time: 9.03154 s
Function: create at line 427

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   427                                               @dispatch(event="provider.storage.volumes.create",
   428                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   429                                               @profile
   430                                               def create(self, label, size, zone, snapshot=None, description=None):
   431        14        175.0     12.5      0.0          OpenStackVolume.assert_valid_resource_label(label)
   432         4          6.0      1.5      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   433         4          3.0      0.8      0.0          snapshot_id = snapshot.id if isinstance(
   434         4          7.0      1.8      0.0              snapshot, OpenStackSnapshot) and snapshot else snapshot
   435                                           
   436         4    2231220.0 557805.0     24.7          os_vol = self.provider.cinder.volumes.create(
   437         4          8.0      2.0      0.0              size, name=label, description=description,
   438         4    6800050.0 1700012.5     75.3              availability_zone=zone_id, snapshot_id=snapshot_id)
   439         4         72.0     18.0      0.0          return OpenStackVolume(self.provider, os_vol)

Total time: 7.15303 s
Function: list at line 493

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   493                                               @dispatch(event="provider.storage.snapshots.list",
   494                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   495                                               @profile
   496                                               def list(self, limit=None, marker=None):
   497                                                   cb_snaps = [
   498         8         15.0      1.9      0.0              OpenStackSnapshot(self.provider, snap) for
   499         8         52.0      6.5      0.0              snap in self.provider.cinder.volume_snapshots.list(
   500         8         18.0      2.2      0.0                  search_opts={'limit': oshelpers.os_result_limit(self.provider,
   501         8        192.0     24.0      0.0                                                                  limit),
   502         8    7152411.0 894051.4    100.0                               'marker': marker})]
   503         8        346.0     43.2      0.0          return oshelpers.to_server_paged_list(self.provider, cb_snaps, limit)

Total time: 6.40756 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         2          2.0      1.0      0.0          obj_list = self
   230         2          2.0      1.0      0.0          filters = ['name']
   231         2    6407505.0 3203752.5    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         2         55.0     27.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 6.38628 s
Function: list at line 942

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   942                                               @dispatch(event="provider.compute.vm_types.list",
   943                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   944                                               @profile
   945                                               def list(self, limit=None, marker=None):
   946                                                   cb_itypes = [
   947         4          5.0      1.2      0.0              OpenStackVMType(self.provider, obj)
   948         4    1932073.0 483018.2     30.3              for obj in self.provider.nova.flavors.list(
   949         4        164.0     41.0      0.0                  limit=oshelpers.os_result_limit(self.provider, limit),
   950         4    4453875.0 1113468.8     69.7                  marker=marker)]
   951                                           
   952         4        159.0     39.8      0.0          return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)

Total time: 5.35269 s
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
   717        23        383.0     16.7      0.0          self.assert_valid_resource_label(value)
   718         7          9.0      1.3      0.0          self._snapshot.name = value
   719         7    5352301.0 764614.4    100.0          self._snapshot.update(name=value or "")

Total time: 4.40069 s
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160         2          6.0      3.0      0.0          try:
  1161         2    4400680.0 2200340.0    100.0              sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162         2          3.0      1.5      0.0              if sn:
  1163         2          4.0      2.0      0.0                  return sn[0]
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

Total time: 4.34049 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         2          2.0      1.0      0.0          if not network:
   313         2          1.0      0.5      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         2          1.0      0.5      0.0          filters = ['label']
   317         2    4340424.0 2170212.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         2         60.0     30.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 4.29626 s
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122         2          2.0      1.0      0.0          if network:
  1123                                                       network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125                                                       subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128         2          2.0      1.0      0.0              subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129         2    4296142.0 2148071.0    100.0                         self.provider.neutron.list_subnets().get('subnets', [])]
  1130         2          9.0      4.5      0.0          return ClientPagedResultList(self.provider, subnets,
  1131         2        107.0     53.5      0.0                                       limit=limit, marker=marker)

Total time: 3.39346 s
Function: delete at line 441

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   441                                               @dispatch(event="provider.storage.volumes.delete",
   442                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   443                                               @profile
   444                                               def delete(self, volume):
   445         5          7.0      1.4      0.0          volume = (volume if isinstance(volume, OpenStackVolume)
   446                                                             else self.get(volume))
   447         5          3.0      0.6      0.0          if volume:
   448                                                       # pylint:disable=protected-access
   449         5    3393451.0 678690.2    100.0              volume._volume.delete()

Total time: 2.72456 s
Function: list at line 415

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   415                                               @dispatch(event="provider.storage.volumes.list",
   416                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   417                                               @profile
   418                                               def list(self, limit=None, marker=None):
   419                                                   cb_vols = [
   420         4          6.0      1.5      0.0              OpenStackVolume(self.provider, vol)
   421         4         22.0      5.5      0.0              for vol in self.provider.cinder.volumes.list(
   422         4         84.0     21.0      0.0                  limit=oshelpers.os_result_limit(self.provider, limit),
   423         4    2724312.0 681078.0    100.0                  marker=marker)]
   424                                           
   425         4        131.0     32.8      0.0          return oshelpers.to_server_paged_list(self.provider, cb_vols, limit)

Total time: 2.53401 s
Function: find at line 469

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   469                                               @dispatch(event="provider.storage.snapshots.find",
   470                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   471                                               @profile
   472                                               def find(self, **kwargs):
   473         6         12.0      2.0      0.0          label = kwargs.pop('label', None)
   474                                           
   475                                                   # All kwargs should have been popped at this time.
   476         6         14.0      2.3      0.0          if len(kwargs) > 0:
   477         2          2.0      1.0      0.0              raise InvalidParamException(
   478         2          1.0      0.5      0.0                  "Unrecognised parameters for search: %s. Supported "
   479         2         28.0     14.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   480                                           
   481         4          4.0      1.0      0.0          search_opts = {'name': label,  # TODO: Cinder is ignoring name
   482         4         82.0     20.5      0.0                         'limit': oshelpers.os_result_limit(self.provider),
   483         4          6.0      1.5      0.0                         'marker': None}
   484         4          5.0      1.2      0.0          log.debug("Searching for an OpenStack snapshot with the following "
   485         4         20.0      5.0      0.0                    "params: %s", search_opts)
   486                                                   cb_snaps = [
   487         4          4.0      1.0      0.0              OpenStackSnapshot(self.provider, snap) for
   488         4    2533658.0 633414.5    100.0              snap in self.provider.cinder.volume_snapshots.list(search_opts)
   489                                                       if snap.name == label]
   490                                           
   491         4        173.0     43.2      0.0          return oshelpers.to_server_paged_list(self.provider, cb_snaps)

Total time: 2.36279 s
Function: create at line 505

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   505                                               @dispatch(event="provider.storage.snapshots.create",
   506                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   507                                               @profile
   508                                               def create(self, label, volume, description=None):
   509        23        332.0     14.4      0.0          OpenStackSnapshot.assert_valid_resource_label(label)
   510         3         11.0      3.7      0.0          volume_id = (volume.id if isinstance(volume, OpenStackVolume)
   511                                                                else volume)
   512                                           
   513         3         18.0      6.0      0.0          os_snap = self.provider.cinder.volume_snapshots.create(
   514         3          2.0      0.7      0.0              volume_id, name=label,
   515         3    2362361.0 787453.7    100.0              description=description)
   516         3         66.0     22.0      0.0          return OpenStackSnapshot(self.provider, os_snap)

Total time: 2.34762 s
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
   589        11        184.0     16.7      0.0          self.assert_valid_resource_label(value)
   590         3          5.0      1.7      0.0          self._volume.name = value
   591         3    2347427.0 782475.7    100.0          self._volume.update(name=value or "")

Total time: 1.84625 s
Function: delete at line 518

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   518                                               @dispatch(event="provider.storage.snapshots.delete",
   519                                                         priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
   520                                               @profile
   521                                               def delete(self, snapshot):
   522         3          5.0      1.7      0.0          s = (snapshot if isinstance(snapshot, OpenStackSnapshot) else
   523                                                        self.get(snapshot))
   524         3          1.0      0.3      0.0          if s:
   525                                                       # pylint:disable=protected-access
   526         3    1846248.0 615416.0    100.0              s._snapshot.delete()

Total time: 1.36465 s
Function: find at line 392

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   392                                               @dispatch(event="provider.storage.volumes.find",
   393                                                         priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
   394                                               @profile
   395                                               def find(self, **kwargs):
   396         3          4.0      1.3      0.0          label = kwargs.pop('label', None)
   397                                           
   398                                                   # All kwargs should have been popped at this time.
   399         3          3.0      1.0      0.0          if len(kwargs) > 0:
   400         1          1.0      1.0      0.0              raise InvalidParamException(
   401         1          1.0      1.0      0.0                  "Unrecognised parameters for search: %s. Supported "
   402         1         13.0     13.0      0.0                  "attributes: %s" % (kwargs, 'label'))
   403                                           
   404         2         16.0      8.0      0.0          log.debug("Searching for an OpenStack Volume with the label %s", label)
   405         2          2.0      1.0      0.0          search_opts = {'name': label}
   406                                                   cb_vols = [
   407         2          3.0      1.5      0.0              OpenStackVolume(self.provider, vol)
   408         2          9.0      4.5      0.0              for vol in self.provider.cinder.volumes.list(
   409         2          1.0      0.5      0.0                  search_opts=search_opts,
   410         2         35.0     17.5      0.0                  limit=oshelpers.os_result_limit(self.provider),
   411         2    1364483.0 682241.5    100.0                  marker=None)]
   412                                           
   413         2         75.0     37.5      0.0          return oshelpers.to_server_paged_list(self.provider, cb_vols)

Total time: 0.712808 s
Function: description at line 725

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   725                                               @description.setter
   726                                               @profile
   727                                               def description(self, value):
   728         1          2.0      2.0      0.0          self._snapshot.description = value
   729         1     712806.0 712806.0    100.0          self._snapshot.update(description=value)

