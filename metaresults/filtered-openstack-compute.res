cloudbridge.test.test_compute_service.CloudComputeServiceTestCase


Error during cleanup: CloudBridgeBaseException: Unable to complete operation on subnet 0b8a4758-2741-4893-a281-c1800b2c5998: One or more ports have an IP allocation from this subnet.
Neutron server returns request_ids: ['req-069e73eb-05f5-4458-b0f6-c91bc62e6446'] from exception type: <class 'neutronclient.common.exceptions.Conflict'>
Error during cleanup: CloudBridgeBaseException: ConflictException: 409: Client Error for url: http://130.56.249.49:9696/v2.0/security-groups/f1d2ea25-5850-4b1f-8789-34cdf4ae2da4, {"NeutronError": {"message": "Security Group f1d2ea25-5850-4b1f-8789-34cdf4ae2da4 in use.", "type": "SecurityGroupInUse", "detail": ""}} from exception type: <class 'openstack.exceptions.ConflictException'>
Test output
 s.EEE.
======================================================================
ERROR: test_crud_instance (cloudbridge.test.test_compute_service.CloudComputeServiceTestCase)
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
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-abda1555-9666-43cc-85d9-f5fe92697d32)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_compute_service.py", line 74, in test_crud_instance
    custom_check_delete=check_deleted)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/standard_interface_tests.py", line 339, in check_crud
    obj = create_func(label)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_compute_service.py", line 47, in create_inst
    subnet=subnet, user_data={})
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
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-abda1555-9666-43cc-85d9-f5fe92697d32) from exception type: <class 'novaclient.exceptions.BadRequest'>

======================================================================
ERROR: test_instance_methods (cloudbridge.test.test_compute_service.CloudComputeServiceTestCase)
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
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-74b2f0be-3720-46c7-b73a-93756e6f272f)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_compute_service.py", line 340, in test_instance_methods
    subnet=subnet)
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
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-74b2f0be-3720-46c7-b73a-93756e6f272f) from exception type: <class 'novaclient.exceptions.BadRequest'>

======================================================================
ERROR: test_instance_properties (cloudbridge.test.test_compute_service.CloudComputeServiceTestCase)
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
novaclient.exceptions.BadRequest: Can not find requested image (HTTP 400) (Request-ID: req-651d0ec1-307c-4760-a55e-aaeeaa505bcd)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/helpers/__init__.py", line 41, in wrapper
    func(self, *args, **kwargs)
  File "/Users/alex/Desktop/work/cloudbridge/cloudbridge/test/test_compute_service.py", line 104, in test_instance_properties
    subnet=subnet)
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
cloudbridge.cloud.interfaces.exceptions.CloudBridgeBaseException: CloudBridgeBaseException: Can not find requested image (HTTP 400) (Request-ID: req-651d0ec1-307c-4760-a55e-aaeeaa505bcd) from exception type: <class 'novaclient.exceptions.BadRequest'>

----------------------------------------------------------------------
Ran 6 tests in 41.244s

FAILED (errors=3, skipped=1)

Wrote profile results to run_single.py.lprof
Timer unit: 1e-06 s

Total time: 13.802 s
Function: create at line 787

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   787                                               @dispatch(event="provider.compute.instances.create",
   788                                                         priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
   789                                               @profile
   790                                               def create(self, label, image, vm_type, subnet, zone,
   791                                                          key_pair=None, vm_firewalls=None, user_data=None,
   792                                                          launch_config=None, **kwargs):
   793        13        189.0     14.5      0.0          OpenStackInstance.assert_valid_resource_label(label)
   794         3         10.0      3.3      0.0          image_id = image.id if isinstance(image, MachineImage) else image
   795                                                   vm_size = vm_type.id if \
   796         3          7.0      2.3      0.0              isinstance(vm_type, VMType) else \
   797         3         20.0      6.7      0.0              self.provider.compute.vm_types.find(
   798         3    7000174.0 2333391.3     50.7                  name=vm_type)[0].id
   799         3         11.0      3.7      0.0          if isinstance(subnet, Subnet):
   800         3         16.0      5.3      0.0              subnet_id = subnet.id
   801         3         11.0      3.7      0.0              net_id = subnet.network_id
   802                                                   else:
   803                                                       subnet_id = subnet
   804                                                       net_id = (self.provider.networking.subnets
   805                                                                 .get(subnet_id).network_id
   806                                                                 if subnet_id else None)
   807         3          8.0      2.7      0.0          zone_id = zone.id if isinstance(zone, PlacementZone) else zone
   808                                                   key_pair_name = key_pair.name if \
   809         3         13.0      4.3      0.0              isinstance(key_pair, KeyPair) else key_pair
   810         3          6.0      2.0      0.0          bdm = None
   811         3          7.0      2.3      0.0          if launch_config:
   812                                                       bdm = self._to_block_device_mapping(launch_config)
   813                                           
   814                                                   # Security groups must be passed in as a list of IDs and attached to a
   815                                                   # port if a port is being created. Otherwise, the security groups must
   816                                                   # be passed in as a list of names to the servers.create() call.
   817                                                   # OpenStack will respect the port's security groups first and then
   818                                                   # fall-back to the named security groups.
   819         3          7.0      2.3      0.0          sg_name_list = []
   820         3          6.0      2.0      0.0          nics = None
   821         3          8.0      2.7      0.0          if subnet_id:
   822         3          9.0      3.0      0.0              log.debug("Creating network port for %s in subnet: %s",
   823         3         23.0      7.7      0.0                        label, subnet_id)
   824         3          7.0      2.3      0.0              sg_list = []
   825         3          6.0      2.0      0.0              if vm_firewalls:
   826         1          3.0      3.0      0.0                  if isinstance(vm_firewalls, list) and \
   827         1          3.0      3.0      0.0                          isinstance(vm_firewalls[0], VMFirewall):
   828         1          2.0      2.0      0.0                      sg_list = vm_firewalls
   829                                                           else:
   830                                                               sg_list = (self.provider.security.vm_firewalls
   831                                                                          .find(label=sg) for sg in vm_firewalls)
   832                                                               sg_list = (sg[0] for sg in sg_list if sg)
   833         3         29.0      9.7      0.0              sg_id_list = [sg.id for sg in sg_list]
   834                                                       port_def = {
   835         3          6.0      2.0      0.0                  "port": {
   836         3          8.0      2.7      0.0                      "admin_state_up": True,
   837         3         10.0      3.3      0.0                      "name": OpenStackInstance._generate_name_from_label(
   838         3        190.0     63.3      0.0                          label, 'cb-port'),
   839         3          6.0      2.0      0.0                      "network_id": net_id,
   840         3          8.0      2.7      0.0                      "fixed_ips": [{"subnet_id": subnet_id}],
   841         3          9.0      3.0      0.0                      "security_groups": sg_id_list
   842                                                           }
   843                                                       }
   844         3    3157095.0 1052365.0     22.9              port_id = self.provider.neutron.create_port(port_def)['port']['id']
   845         3         16.0      5.3      0.0              nics = [{'net-id': net_id, 'port-id': port_id}]
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
   856         3         35.0     11.7      0.0          log.debug("Launching in subnet %s", subnet_id)
   857         3         36.0     12.0      0.0          os_instance = self.provider.nova.servers.create(
   858         3          8.0      2.7      0.0              label,
   859         3         16.0      5.3      0.0              None if self._has_root_device(launch_config) else image_id,
   860         3          8.0      2.7      0.0              vm_size,
   861         3          8.0      2.7      0.0              min_count=1,
   862         3          8.0      2.7      0.0              max_count=1,
   863         3          8.0      2.7      0.0              availability_zone=zone_id,
   864         3          8.0      2.7      0.0              key_name=key_pair_name,
   865         3          8.0      2.7      0.0              security_groups=sg_name_list,
   866         3         13.0      4.3      0.0              userdata=str(user_data) or None,
   867         3          8.0      2.7      0.0              block_device_mapping_v2=bdm,
   868         3    3643903.0 1214634.3     26.4              nics=nics)
   869                                                   return OpenStackInstance(self.provider, os_instance)

Total time: 9.72766 s
Function: find at line 225

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   225                                               @dispatch(event="provider.compute.vm_types.find",
   226                                                         priority=BaseCloudService.STANDARD_EVENT_PRIORITY)
   227                                               @profile
   228                                               def find(self, **kwargs):
   229         4          4.0      1.0      0.0          obj_list = self
   230         4          3.0      0.8      0.0          filters = ['name']
   231         4    9727539.0 2431884.8    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   232         4        118.0     29.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 9.66376 s
Function: list at line 942

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   942                                               @dispatch(event="provider.compute.vm_types.list",
   943                                                         priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
   944                                               @profile
   945                                               def list(self, limit=None, marker=None):
   946                                                   cb_itypes = [
   947         8         10.0      1.2      0.0              OpenStackVMType(self.provider, obj)
   948         8    1864288.0 233036.0     19.3              for obj in self.provider.nova.flavors.list(
   949         8        236.0     29.5      0.0                  limit=oshelpers.os_result_limit(self.provider, limit),
   950         8    7798932.0 974866.5     80.7                  marker=marker)]
   951                                           
   952         8        292.0     36.5      0.0          return oshelpers.to_server_paged_list(self.provider, cb_itypes, limit)

Total time: 4.68956 s
Function: delete at line 1083

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1083                                               @dispatch(event="provider.networking.networks.delete",
  1084                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1085                                               @profile
  1086                                               def delete(self, network):
  1087         1          3.0      3.0      0.0          network = (network if isinstance(network, OpenStackNetwork) else
  1088                                                              self.get(network))
  1089         1          1.0      1.0      0.0          if not network:
  1090                                                       return
  1091         1          7.0      7.0      0.0          if not network.external and network.id in str(
  1092         1     358126.0 358126.0      7.6                  self.provider.neutron.list_networks()):
  1093                                                       # If there are ports associated with the network, it won't delete
  1094         1          8.0      8.0      0.0              ports = self.provider.neutron.list_ports(
  1095         1     441220.0 441220.0      9.4                  network_id=network.id).get('ports', [])
  1096         3          8.0      2.7      0.0              for port in ports:
  1097         2          2.0      1.0      0.0                  try:
  1098         2    1842265.0 921132.5     39.3                      self.provider.neutron.delete_port(port.get('id'))
  1099                                                           except PortNotFoundClient:
  1100                                                               # Ports could have already been deleted if instances
  1101                                                               # are terminated etc. so exceptions can be safely ignored
  1102                                                               pass
  1103         1    2047921.0 2047921.0     43.7              self.provider.neutron.delete_network(network.id)

Total time: 3.89371 s
Function: list at line 1118

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1118                                               @dispatch(event="provider.networking.subnets.list",
  1119                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1120                                               @profile
  1121                                               def list(self, network=None, limit=None, marker=None):
  1122         4          5.0      1.2      0.0          if network:
  1123         1          4.0      4.0      0.0              network_id = (network.id if isinstance(network, OpenStackNetwork)
  1124                                                                     else network)
  1125         1         47.0     47.0      0.0              subnets = [subnet for subnet in self if network_id ==
  1126                                                                  subnet.network_id]
  1127                                                   else:
  1128         3          3.0      1.0      0.0              subnets = [OpenStackSubnet(self.provider, subnet) for subnet in
  1129         3    3893477.0 1297825.7    100.0                         self.provider.neutron.list_subnets().get('subnets', [])]
  1130         4         15.0      3.8      0.0          return ClientPagedResultList(self.provider, subnets,
  1131         4        163.0     40.8      0.0                                       limit=limit, marker=marker)

Total time: 3.58635 s
Function: get_or_create_default at line 1155

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1155                                               @profile
  1156                                               def get_or_create_default(self, zone):
  1157                                                   """
  1158                                                   Subnet zone is not supported by OpenStack and is thus ignored.
  1159                                                   """
  1160         2          4.0      2.0      0.0          try:
  1161         2    3586339.0 1793169.5    100.0              sn = self.find(label=OpenStackSubnet.CB_DEFAULT_SUBNET_LABEL)
  1162         2          3.0      1.5      0.0              if sn:
  1163         2          3.0      1.5      0.0                  return sn[0]
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

Total time: 3.56473 s
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
   317         2    3564667.0 1782333.5    100.0          matches = cb_helpers.generic_find(filters, kwargs, obj_list)
   318         2         59.0     29.5      0.0          return ClientPagedResultList(self._provider, list(matches))

Total time: 3.46815 s
Function: create at line 1071

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1071                                               @dispatch(event="provider.networking.networks.create",
  1072                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1073                                               @profile
  1074                                               def create(self, label, cidr_block):
  1075         1          8.0      8.0      0.0          OpenStackNetwork.assert_valid_resource_label(label)
  1076         1          1.0      1.0      0.0          net_info = {'name': label or ""}
  1077         1    2225770.0 2225770.0     64.2          network = self.provider.neutron.create_network({'network': net_info})
  1078         1         38.0     38.0      0.0          cb_net = OpenStackNetwork(self.provider, network.get('network'))
  1079         1          1.0      1.0      0.0          if label:
  1080         1    1242335.0 1242335.0     35.8              cb_net.label = label
  1081         1          1.0      1.0      0.0          return cb_net

Total time: 3.09715 s
Function: create at line 190

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   190                                               @dispatch(event="provider.security.key_pairs.create",
   191                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   192                                               @profile
   193                                               def create(self, name, public_key_material=None):
   194         1          8.0      8.0      0.0          OpenStackKeyPair.assert_valid_resource_name(name)
   195         1    2450763.0 2450763.0     79.1          existing_kp = self.find(name=name)
   196         1          1.0      1.0      0.0          if existing_kp:
   197                                                       raise DuplicateResourceException(
   198                                                           'Keypair already exists with name {0}'.format(name))
   199                                           
   200         1          1.0      1.0      0.0          private_key = None
   201         1          1.0      1.0      0.0          if not public_key_material:
   202         1      81076.0  81076.0      2.6              public_key_material, private_key = cb_helpers.generate_key_pair()
   203                                           
   204         1          7.0      7.0      0.0          kp = self.provider.nova.keypairs.create(name,
   205         1     565276.0 565276.0     18.3                                                  public_key=public_key_material)
   206         1         15.0     15.0      0.0          cb_kp = OpenStackKeyPair(self.provider, kp)
   207         1          3.0      3.0      0.0          cb_kp.material = private_key
   208         1          1.0      1.0      0.0          return cb_kp

Total time: 3.02151 s
Function: get at line 690

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   690                                               @profile
   691                                               def get(self, image_id):
   692                                                   """
   693                                                   Returns an Image given its id
   694                                                   """
   695         1         10.0     10.0      0.0          log.debug("Getting OpenStack Image with the id: %s", image_id)
   696         1          0.0      0.0      0.0          try:
   697         1          0.0      0.0      0.0              return OpenStackMachineImage(
   698         1    3021456.0 3021456.0    100.0                  self.provider, self.provider.os_conn.image.get_image(image_id))
   699         1          3.0      3.0      0.0          except (NotFoundException, ResourceNotFound):
   700         1         10.0     10.0      0.0              log.debug("Image %s not found", image_id)
   701         1         36.0     36.0      0.0              return None

Total time: 2.4398 s
Function: find at line 172

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   172                                               @dispatch(event="provider.security.key_pairs.find",
   173                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   174                                               @profile
   175                                               def find(self, **kwargs):
   176         1          1.0      1.0      0.0          name = kwargs.pop('name', None)
   177                                           
   178                                                   # All kwargs should have been popped at this time.
   179         1          1.0      1.0      0.0          if len(kwargs) > 0:
   180                                                       raise InvalidParamException(
   181                                                           "Unrecognised parameters for search: %s. Supported "
   182                                                           "attributes: %s" % (kwargs, 'name'))
   183                                           
   184         1    2439732.0 2439732.0    100.0          keypairs = self.provider.nova.keypairs.findall(name=name)
   185         1          4.0      4.0      0.0          results = [OpenStackKeyPair(self.provider, kp)
   186         1          3.0      3.0      0.0                     for kp in keypairs]
   187         1         12.0     12.0      0.0          log.debug("Searching for %s in: %s", name, keypairs)
   188         1         46.0     46.0      0.0          return ClientPagedResultList(self.provider, results)

Total time: 2.07037 s
Function: create at line 250

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   250                                               @cb_helpers.deprecated_alias(network_id='network')
   251                                               @dispatch(event="provider.security.vm_firewalls.create",
   252                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   253                                               @profile
   254                                               def create(self, label, network, description=None):
   255         1          8.0      8.0      0.0          OpenStackVMFirewall.assert_valid_resource_label(label)
   256         1          1.0      1.0      0.0          net_id = network.id if isinstance(network, Network) else network
   257                                                   # We generally simulate a network being associated with a firewall
   258                                                   # by storing the supplied value in the firewall description field that
   259                                                   # is not modifiable after creation; however, because of some networking
   260                                                   # specificity in Nectar, we must also allow an empty network id value.
   261         1          1.0      1.0      0.0          if not net_id:
   262                                                       net_id = ""
   263         1          1.0      1.0      0.0          if not description:
   264                                                       description = ""
   265         1          1.0      1.0      0.0          description += " [{}{}]".format(OpenStackVMFirewall._network_id_tag,
   266         1          3.0      3.0      0.0                                          net_id)
   267         1    1260211.0 1260211.0     60.9          sg = self.provider.os_conn.network.create_security_group(
   268         1     810110.0 810110.0     39.1              name=label, description=description)
   269         1          2.0      2.0      0.0          if sg:
   270         1         30.0     30.0      0.0              return OpenStackVMFirewall(self.provider, sg)
   271                                                   return None

Total time: 1.72135 s
Function: get at line 1035

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1035                                               @dispatch(event="provider.networking.networks.get",
  1036                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1037                                               @profile
  1038                                               def get(self, network_id):
  1039         4         13.0      3.2      0.0          network = (n for n in self if n.id == network_id)
  1040         4    1721333.0 430333.2    100.0          return next(network, None)

Total time: 1.69941 s
Function: list at line 1042

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1042                                               @dispatch(event="provider.networking.networks.list",
  1043                                                         priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
  1044                                               @profile
  1045                                               def list(self, limit=None, marker=None):
  1046         4          5.0      1.2      0.0          networks = [OpenStackNetwork(self.provider, network)
  1047         4    1698958.0 424739.5    100.0                      for network in self.provider.neutron.list_networks()
  1048         4        280.0     70.0      0.0                      .get('networks') if network]
  1049         4          9.0      2.2      0.0          return ClientPagedResultList(self.provider, networks,
  1050         4        157.0     39.2      0.0                                       limit=limit, marker=marker)

Total time: 1.343 s
Function: refresh at line 842

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   842                                               @profile
   843                                               def refresh(self):
   844                                                   """Refresh the state of this network by re-querying the provider."""
   845         3    1342994.0 447664.7    100.0          network = self._provider.networking.networks.get(self.id)
   846         3          3.0      1.0      0.0          if network:
   847                                                       # pylint:disable=protected-access
   848         1          2.0      2.0      0.0              self._network = network._network
   849                                                   else:
   850                                                       # Network no longer exists
   851         2          4.0      2.0      0.0              self._network = {}

Total time: 1.24232 s
Function: label at line 811

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   811                                               @label.setter
   812                                               @profile
   813                                               def label(self, value):
   814                                                   """
   815                                                   Set the network label.
   816                                                   """
   817         1          9.0      9.0      0.0          self.assert_valid_resource_label(value)
   818         1          6.0      6.0      0.0          self._provider.neutron.update_network(
   819         1     832175.0 832175.0     67.0              self.id, {'network': {'name': value or ""}})
   820         1     410128.0 410128.0     33.0          self.refresh()

Total time: 0.560666 s
Function: create at line 1133

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1133                                               @dispatch(event="provider.networking.subnets.create",
  1134                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1135                                               @profile
  1136                                               def create(self, label, network, cidr_block, zone):
  1137                                                   """zone param is ignored."""
  1138         1          9.0      9.0      0.0          OpenStackSubnet.assert_valid_resource_label(label)
  1139         1          3.0      3.0      0.0          network_id = (network.id if isinstance(network, OpenStackNetwork)
  1140                                                                 else network)
  1141         1          1.0      1.0      0.0          subnet_info = {'name': label, 'network_id': network_id,
  1142         1          1.0      1.0      0.0                         'cidr': cidr_block, 'ip_version': 4}
  1143         1     560631.0 560631.0    100.0          subnet = (self.provider.neutron.create_subnet({'subnet': subnet_info})
  1144         1          3.0      3.0      0.0                    .get('subnet'))
  1145         1         17.0     17.0      0.0          cb_subnet = OpenStackSubnet(self.provider, subnet)
  1146         1          1.0      1.0      0.0          return cb_subnet

Total time: 0.510433 s
Function: delete at line 210

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   210                                               @dispatch(event="provider.security.key_pairs.delete",
   211                                                         priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
   212                                               @profile
   213                                               def delete(self, key_pair):
   214         1          3.0      3.0      0.0          keypair = (key_pair if isinstance(key_pair, OpenStackKeyPair)
   215                                                              else self.get(key_pair))
   216         1          1.0      1.0      0.0          if keypair:
   217                                                       # pylint:disable=protected-access
   218         1     510429.0 510429.0    100.0              keypair._key_pair.delete()

Total time: 0.3819 s
Function: delete at line 1148

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
  1148                                               @dispatch(event="provider.networking.subnets.delete",
  1149                                                         priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
  1150                                               @profile
  1151                                               def delete(self, subnet):
  1152         1          4.0      4.0      0.0          sn_id = subnet.id if isinstance(subnet, OpenStackSubnet) else subnet
  1153         1     381896.0 381896.0    100.0          self.provider.neutron.delete_subnet(sn_id)

Total time: 0.36989 s
Function: delete at line 273

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   273                                               @dispatch(event="provider.security.vm_firewalls.delete",
   274                                                         priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
   275                                               @profile
   276                                               def delete(self, vm_firewall):
   277         1          3.0      3.0      0.0          fw = (vm_firewall if isinstance(vm_firewall, OpenStackVMFirewall)
   278                                                         else self.get(vm_firewall))
   279         1          1.0      1.0      0.0          if fw:
   280                                                       # pylint:disable=protected-access
   281         1     369886.0 369886.0    100.0              fw._vm_firewall.delete(self.provider.os_conn.session)

Total time: 7e-06 s
Function: create_launch_config at line 783

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
   783                                               @profile
   784                                               def create_launch_config(self):
   785         1          7.0      7.0    100.0          return BaseLaunchConfig(self.provider)

