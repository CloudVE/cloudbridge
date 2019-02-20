cloudbridge.test.test_image_service.CloudImageServiceTestCase


Test output
 E.
======================================================================
ERROR: test_create_and_list_image (cloudbridge.test.test_image_service.CloudImageServiceTestCase)
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
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-2915ef94-96b5-4340-98ea-ad8cb17ab604)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_image_service.py", line 95, in test_create_and_list_image
    self.provider, instance_label, subnet=subnet)
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
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-2915ef94-96b5-4340-98ea-ad8cb17ab604) from exception type: <class 'novaclient.exceptions.BadRequest'>

----------------------------------------------------------------------
Ran 2 tests in 7.575s

FAILED (errors=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 4.28762 s
Function: create at line 787

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   787                                               @dispatch(event="provider.compute.instances.create",
   788                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   789                                               @profile
   790                                               def create(self, label, image, vm_type, subnet, zone,
   791                                                          key_pair=None, vm_firewalls=None, user_data=None,
   792                                                          launch_config=None, **kwargs):
   793         1         11.0     11.0      0.0          OpenStackInstance.assert_valid_resource_label(label)
   794         1          4.0      4.0      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   795                                                   vm_size = vm_type.id if \
   796         1          3.0      3.0      0.0              isinstance(vm_type, VMType) else \
   797         1          7.0      7.0      0.0              self.provider.compute.vm_types.find(
   798         1    2657546.0 2657546.0     62.0                  name=vm_type)[0].id
   799         1          3.0      3.0      0.0          if isinstance(subnet, Subnet):
   800         1          5.0      5.0      0.0              subnet_id = subnet.id
   801         1          4.0      4.0      0.0              net_id = subnet.network_id
   802                                                   else:
   803                                                       subnet_id = subnet
   804                                                       net_id = (self.provider.networking.subnets
   805                                                                 .get(subnet_id).network_id
   806                                                                 if subnet_id else None)
   807         1          2.0      2.0      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   808                                                   key_pair_name = key_pair.name if \
   809         1          2.0      2.0      0.0              isinstance(key_pair, KeyPair) else key_pair
   810         1          2.0      2.0      0.0          bdm = None
   811         1          2.0      2.0      0.0          if launch_config:
   812                                                       bdm = self._to_block_device_mapping(launch_config)
   813                                           
   814                                                   # Security groups must be passed in as a list of IDs and attached to a
   815                                                   # port if a port is being created. Otherwise, the security groups must
   816                                                   # be passed in as a list of names to the servers.create() call.
   817                                                   # OpenStack will respect the port's security groups first and then
   818                                                   # fall-back to the named security groups.
   819         1          2.0      2.0      0.0          sg_name_list = []
   820         1          2.0      2.0      0.0          nics = None
   821         1          2.0      2.0      0.0          if subnet_id:
   822         1          2.0      2.0      0.0              log.debug("Creating network port for %s in subnet: %s",
   823         1          7.0      7.0      0.0                        label, subnet_id)
   824         1          2.0      2.0      0.0              sg_list = []
   825         1          2.0      2.0      0.0              if vm_firewalls:
   826                                                           if isinstance(vm_firewalls, list) and \
   827                                                                   isinstance(vm_firewalls[0], VMFirewall):
   828                                                               sg_list = vm_firewalls
   829                                                           else:
   830                                                               sg_list = (self.provider.security.vm_firewalls
   831                                                                          .find(label=sg) for sg in vm_firewalls)
   832                                                               sg_list = (sg[0] for sg in sg_list if sg)
   833         1          3.0      3.0      0.0              sg_id_list = [sg.id for sg in sg_list]
   834                                                       port_def = {
   835         1          2.0      2.0      0.0                  "port": {
   836         1          2.0      2.0      0.0                      "admin_state_up": True,
   837         1          3.0      3.0      0.0                      "name": OpenStackInstance._generate_name_from_label(
   838         1         54.0     54.0      0.0                          label, 'cb-port'),
   839         1          2.0      2.0      0.0                      "network_id": net_id,
   840         1          3.0      3.0      0.0                      "fixed_ips": [{"subnet_id": subnet_id}],
   841         1          2.0      2.0      0.0                      "security_groups": sg_id_list
   842                                                           }
   843                                                       }
   844         1     867800.0 867800.0     20.2              port_id = self.provider.neutron.create_port(port_def)['port']['id']
   845         1          5.0      5.0      0.0              nics = [{'net-id': net_id, 'port-id': port_id}]
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
   856         1         14.0     14.0      0.0          log.debug("Launching in subnet %s", subnet_id)
   857         1         15.0     15.0      0.0          os_instance = self.provider.nova.servers.create(
   858         1          3.0      3.0      0.0              label,
   859         1          6.0      6.0      0.0              None if self._has_root_device(launch_config) else image_id,
   860         1          3.0      3.0      0.0              vm_size,
   861         1          3.0      3.0      0.0              min_count=1,
   862         1          3.0      3.0      0.0              max_count=1,
   863         1          3.0      3.0      0.0              availability_zone=zone_id,
   864         1          3.0      3.0      0.0              key_name=key_pair_name,
   865         1          3.0      3.0      0.0              security_groups=sg_name_list,
   866         1          4.0      4.0      0.0              userdata=str(user_data) or None,
   867         1          3.0      3.0      0.0              block_device_mapping_v2=bdm,
   868         1     762070.0 762070.0     17.8              nics=nics)
   869                                                   return OpenStackInstance(self.provider, os_instance)

Total time: 2.64646 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         1          1.0      1.0      0.0          obj_list = self
   230         1          0.0      0.0      0.0          filters = ['name']
   231         1    2646438.0 2646438.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         1         23.0     23.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 2.63619 s
Function: list at line 942

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   942                                               @dispatch(event="provider.compute.vm_types.list",
   943                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   944                                               @profile
   945                                               def list(self, limit=None, marker=None):
   946                                                   cb_itypes = [
   947         2          3.0      1.5      0.0              OpenStackVMType(self.provider, obj)
   948         2     718884.0 359442.0     27.3              for obj in self.provider.nova.flavors.list(
   949         2        102.0     51.0      0.0                  limit=oshelpers.os_result_limit(self.provider, limit),
   950         2    1917130.0 958565.0     72.7                  marker=marker)]
   951                                           
   952         2         72.0     36.0      0.0          return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)

Total time: 2.16612 s
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160         1          5.0      5.0      0.0          try:
  1161         1    2166111.0 2166111.0    100.0              sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162         1          1.0      1.0      0.0              if sn:
  1163         1          2.0      2.0      0.0                  return sn[0]
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

Total time: 2.11504 s
Function: find at line 308

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   308                                               @dispatch(event="provider.networking.subnets.find",
   309                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   310                                               @profile
   311                                               def find(self, network=None, **kwargs):
   312         1          1.0      1.0      0.0          if not network:
   313         1          0.0      0.0      0.0              obj_list = self
   314                                                   else:
   315                                                       obj_list = network.subnets
   316         1          0.0      0.0      0.0          filters = ['label']
   317         1    2115016.0 2115016.0    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         1         27.0     27.0      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 2.07967 s
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122         1          1.0      1.0      0.0          if network:
  1123                                                       network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125                                                       subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128         1          2.0      2.0      0.0              subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129         1    2079607.0 2079607.0    100.0                         self.provider.neutron.list_subnets().get('subnets', [])]
  1130         1          3.0      3.0      0.0          return ClientPagedResultList(self.provider, subnets,
  1131         1         58.0     58.0      0.0                                       limit=limit, marker=marker)

