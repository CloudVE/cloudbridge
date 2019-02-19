import io
import ipaddress
import json
import logging
import time
import uuid

import googleapiclient

from cloudbridge.cloud.base import helpers as cb_helpers
from cloudbridge.cloud.base.middleware import dispatch
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBucketObjectService
from cloudbridge.cloud.base.services import BaseBucketService
from cloudbridge.cloud.base.services import BaseComputeService
from cloudbridge.cloud.base.services import BaseFloatingIPService
from cloudbridge.cloud.base.services import BaseGatewayService
from cloudbridge.cloud.base.services import BaseImageService
from cloudbridge.cloud.base.services import BaseInstanceService
from cloudbridge.cloud.base.services import BaseKeyPairService
from cloudbridge.cloud.base.services import BaseNetworkService
from cloudbridge.cloud.base.services import BaseNetworkingService
from cloudbridge.cloud.base.services import BaseRegionService
from cloudbridge.cloud.base.services import BaseRouterService
from cloudbridge.cloud.base.services import BaseSecurityService
from cloudbridge.cloud.base.services import BaseSnapshotService
from cloudbridge.cloud.base.services import BaseStorageService
from cloudbridge.cloud.base.services import BaseSubnetService
from cloudbridge.cloud.base.services import BaseVMFirewallRuleService
from cloudbridge.cloud.base.services import BaseVMFirewallService
from cloudbridge.cloud.base.services import BaseVMTypeService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions import DuplicateResourceException
from cloudbridge.cloud.interfaces.exceptions import InvalidParamException
from cloudbridge.cloud.interfaces.resources import TrafficDirection
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.providers.gcp import helpers

from .resources import GCPBucket
from .resources import GCPBucketObject
from .resources import GCPFirewallsDelegate
from .resources import GCPFloatingIP
from .resources import GCPInstance
from .resources import GCPInternetGateway
from .resources import GCPKeyPair
from .resources import GCPLaunchConfig
from .resources import GCPMachineImage
from .resources import GCPNetwork
from .resources import GCPRegion
from .resources import GCPRouter
from .resources import GCPSnapshot
from .resources import GCPSubnet
from .resources import GCPVMFirewall
from .resources import GCPVMFirewallRule
from .resources import GCPVMType
from .resources import GCPVolume

log = logging.getLogger(__name__)


class GCPSecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(GCPSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = GCPKeyPairService(provider)
        self._vm_firewalls = GCPVMFirewallService(provider)
        self._vm_firewall_rule_svc = GCPVMFirewallRuleService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self):
        return self._vm_firewall_rule_svc


class GCPKeyPairService(BaseKeyPairService):

    def __init__(self, provider):
        super(GCPKeyPairService, self).__init__(provider)

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id):
        """
        Returns a KeyPair given its ID.
        """
        for kp in self:
            if kp.id == key_pair_id:
                return kp
        else:
            return None

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        key_pairs = []
        for item in helpers.find_matching_metadata_items(
                self.provider, GCPKeyPair.KP_TAG_REGEX):
            metadata_value = json.loads(item['value'])
            kp_info = GCPKeyPair.GCPKeyInfo(**metadata_value)
            key_pairs.append(GCPKeyPair(self.provider, kp_info))
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        """
        Searches for a key pair by a given list of attributes.
        """
        obj_list = self
        filters = ['id', 'name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(self.provider,
                                     matches if matches else [])

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name, public_key_material=None):
        GCPKeyPair.assert_valid_resource_name(name)
        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()
        # TODO: Add support for other formats not assume ssh-rsa
        elif "ssh-rsa" not in public_key_material:
            public_key_material = "ssh-rsa {}".format(public_key_material)
        kp_info = GCPKeyPair.GCPKeyInfo(name, public_key_material)
        metadata_value = json.dumps(kp_info._asdict())
        try:
            helpers.add_metadata_item(self.provider,
                                      GCPKeyPair.KP_TAG_PREFIX + name,
                                      metadata_value)
            return GCPKeyPair(self.provider, kp_info, private_key)
        except googleapiclient.errors.HttpError as err:
            if err.resp.get('content-type', '').startswith('application/json'):
                message = (json.loads(err.content).get('error', {})
                           .get('errors', [{}])[0].get('message'))
                if "duplicate keys" in message:
                    raise DuplicateResourceException(
                        'A KeyPair with name {0} already exists'.format(name))
            raise

    @dispatch(event="provider.security.key_pairs.delete",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def delete(self, key_pair):
        key_pair = (key_pair if isinstance(key_pair, GCPKeyPair) else
                    self.get(key_pair))
        if key_pair:
            helpers.remove_metadata_item(
                self.provider, GCPKeyPair.KP_TAG_PREFIX + key_pair.name)


class GCPVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(GCPVMFirewallService, self).__init__(provider)
        self._delegate = GCPFirewallsDelegate(provider)

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id):
        tag, network_name = \
            self._delegate.get_tag_network_from_id(vm_firewall_id)
        if tag is None:
            return None
        network = self.provider.networking.networks.get(network_name)
        return GCPVMFirewall(self._delegate, tag, network)

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        vm_firewalls = []
        for tag, network_name in self._delegate.tag_networks:
            network = self.provider.networking.networks.get(
                    network_name)
            vm_firewall = GCPVMFirewall(self._delegate, tag, network)
            vm_firewalls.append(vm_firewall)
        return ClientPagedResultList(self.provider, vm_firewalls,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.vm_firewalls.create",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, description=None):
        GCPVMFirewall.assert_valid_resource_label(label)
        network = (network if isinstance(network, GCPNetwork)
                   else self.provider.networking.networks.get(network))
        fw = GCPVMFirewall(self._delegate, label, network, description)
        fw.label = label
        # This rule exists implicitly. Add it explicitly so that the firewall
        # is not empty and the rule is shown by list/get/find methods.
        # pylint:disable=protected-access
        self.provider.security._vm_firewall_rules.create_with_priority(
            fw, direction=TrafficDirection.OUTBOUND, protocol='tcp',
            priority=65534, cidr='0.0.0.0/0')
        return fw

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall):
        fw_id = (vm_firewall.id if isinstance(vm_firewall, GCPVMFirewall)
                 else vm_firewall)
        return self._delegate.delete_tag_network_with_id(fw_id)

    def find_by_network_and_tags(self, network_name, tags):
        """
        Finds non-empty VM firewalls by network name and VM firewall names
        (tags). If no matching VM firewall is found, an empty list is returned.
        """
        vm_firewalls = []
        for tag, net_name in self._delegate.tag_networks:
            if network_name != net_name:
                continue
            if tag not in tags:
                continue
            network = self.provider.networking.networks.get(net_name)
            vm_firewalls.append(
                GCPVMFirewall(self._delegate, tag, network))
        return vm_firewalls


class GCPVMFirewallRuleService(BaseVMFirewallRuleService):

    def __init__(self, provider):
        super(GCPVMFirewallRuleService, self).__init__(provider)
        self._dummy_rule = None

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall, limit=None, marker=None):
        rules = []
        for fw in firewall.delegate.iter_firewalls(
                firewall.name, firewall.network.name):
            rule = GCPVMFirewallRule(firewall, fw['id'])
            if rule.is_dummy_rule():
                self._dummy_rule = rule
            else:
                rules.append(rule)
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @property
    def dummy_rule(self):
        if not self._dummy_rule:
            self.list()
        return self._dummy_rule

    @staticmethod
    def to_port_range(from_port, to_port):
        if from_port is not None and to_port is not None:
            return '%d-%d' % (from_port, to_port)
        elif from_port is not None:
            return from_port
        else:
            return to_port

    def create_with_priority(self, firewall, direction, protocol, priority,
                             from_port=None, to_port=None, cidr=None,
                             src_dest_fw=None):
        port = GCPVMFirewallRuleService.to_port_range(from_port, to_port)
        src_dest_tag = None
        src_dest_fw_id = None
        if src_dest_fw:
            src_dest_tag = src_dest_fw.name
            src_dest_fw_id = src_dest_fw.id
        if not firewall.delegate.add_firewall(
                firewall.name, direction, protocol, priority, port, cidr,
                src_dest_tag, firewall.description,
                firewall.network.name):
            return None
        rules = self.find(firewall, direction=direction, protocol=protocol,
                          from_port=from_port, to_port=to_port, cidr=cidr,
                          src_dest_fw_id=src_dest_fw_id)
        if len(rules) < 1:
            return None
        return rules[0]

    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall, direction, protocol, from_port=None,
               to_port=None, cidr=None, src_dest_fw=None):
        return self.create_with_priority(firewall, direction, protocol,
                                         1000, from_port, to_port, cidr,
                                         src_dest_fw)

    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall, rule):
        rule = (rule if isinstance(rule, GCPVMFirewallRule)
                else self.get(firewall, rule))
        if rule.is_dummy_rule():
            return True
        firewall.delegate.delete_firewall_id(rule._rule)


class GCPVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(GCPVMTypeService, self).__init__(provider)

    @property
    def instance_data(self):
        response = (self.provider
                        .gcp_compute
                        .machineTypes()
                        .list(project=self.provider.project_name,
                              zone=self.provider.zone_name)
                        .execute())
        return response['items']

    @dispatch(event="provider.compute.vm_types.get",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_type_id):
        vm_type = self.provider.get_resource('machineTypes', vm_type_id)
        return GCPVMType(self.provider, vm_type) if vm_type else None

    @dispatch(event="provider.compute.vm_types.find",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs):
        matched_inst_types = []
        for inst_type in self.instance_data:
            is_match = True
            for key, value in kwargs.items():
                if key not in inst_type:
                    raise InvalidParamException(
                        "Unrecognised parameters for search: %s." % key)
                if inst_type.get(key) != value:
                    is_match = False
                    break
            if is_match:
                matched_inst_types.append(
                    GCPVMType(self.provider, inst_type))
        return matched_inst_types

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        inst_types = [GCPVMType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class GCPRegionService(BaseRegionService):

    def __init__(self, provider):
        super(GCPRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id):
        region = self.provider.get_resource('regions', region_id,
                                            region=region_id)
        return GCPRegion(self.provider, region) if region else None

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        regions_response = (self.provider
                                .gcp_compute
                                .regions()
                                .list(project=self.provider.project_name,
                                      maxResults=max_result,
                                      pageToken=marker)
                                .execute())
        regions = [GCPRegion(self.provider, region)
                   for region in regions_response['items']]
        if len(regions) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(regions))
        return ServerPagedResultList('nextPageToken' in regions_response,
                                     regions_response.get('nextPageToken'),
                                     False, data=regions)

    @property
    def current(self):
        return self.get(self.provider.region_name)


class GCPImageService(BaseImageService):

    def __init__(self, provider):
        super(GCPImageService, self).__init__(provider)
        self._public_images = None

    _PUBLIC_IMAGE_PROJECTS = ['centos-cloud', 'coreos-cloud', 'debian-cloud',
                              'opensuse-cloud', 'ubuntu-os-cloud', 'cos-cloud']

    def _retrieve_public_images(self):
        if self._public_images is not None:
            return
        self._public_images = []
        for project in GCPImageService._PUBLIC_IMAGE_PROJECTS:
            for image in helpers.iter_all(
                    self.provider.gcp_compute.images(), project=project):
                self._public_images.append(
                    GCPMachineImage(self.provider, image))

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        image = self.provider.get_resource('images', image_id)
        if image:
            return GCPMachineImage(self.provider, image)
        self._retrieve_public_images()
        for public_image in self._public_images:
            if public_image.id == image_id or public_image.name == image_id:
                return public_image
        return None

    def find(self, limit=None, marker=None, **kwargs):
        """
        Searches for an image by a given list of attributes
        """
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        # Retrieve all available images by setting limit to sys.maxsize
        images = [image for image in self if image.label == label]
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        self._retrieve_public_images()
        images = []
        if (self.provider.project_name not in
                GCPImageService._PUBLIC_IMAGE_PROJECTS):
            for image in helpers.iter_all(
                    self.provider.gcp_compute.images(),
                    project=self.provider.project_name):
                images.append(GCPMachineImage(self.provider, image))
        images.extend(self._public_images)
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class GCPInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(GCPInstanceService, self).__init__(provider)

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label, image, vm_type, subnet,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        """
        Creates a new virtual machine instance.
        """
        GCPInstance.assert_valid_resource_name(label)
        zone_name = self.provider.zone_name
        if not isinstance(vm_type, GCPVMType):
            vm_type = self.provider.compute.vm_types.get(vm_type)

        network_interface = {'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                                                'name': 'External NAT'}]}
        if subnet:
            network_interface['subnetwork'] = subnet.id
        else:
            network_interface['network'] = 'global/networks/default'

        num_roots = 0
        disks = []
        boot_disk = None
        if isinstance(launch_config, GCPLaunchConfig):
            for disk in launch_config.block_devices:
                if not disk.source:
                    volume_name = 'disk-{0}'.format(uuid.uuid4())
                    volume_size = disk.size if disk.size else 1
                    volume = self.provider.storage.volumes.create(
                        volume_name, volume_size)
                    volume.wait_till_ready()
                    source_field = 'source'
                    source_value = volume.id
                elif isinstance(disk.source, GCPMachineImage):
                    source_field = 'initializeParams'
                    # Explicitly set diskName; otherwise, instance label will
                    # be used by default which may collide with existing disks.
                    source_value = {
                        'sourceImage': disk.source.id,
                        'diskName': 'image-disk-{0}'.format(uuid.uuid4()),
                        'diskSizeGb': disk.size if disk.size else 20}
                elif isinstance(disk.source, GCPVolume):
                    source_field = 'source'
                    source_value = disk.source.id
                elif isinstance(disk.source, GCPSnapshot):
                    volume = disk.source.create_volume(size=disk.size)
                    volume.wait_till_ready()
                    source_field = 'source'
                    source_value = volume.id
                else:
                    log.warning('Unknown disk source')
                    continue
                autoDelete = True
                if disk.delete_on_terminate is not None:
                    autoDelete = disk.delete_on_terminate
                num_roots += 1 if disk.is_root else 0
                if disk.is_root and not boot_disk:
                    boot_disk = {'boot': True,
                                 'autoDelete': autoDelete,
                                 source_field: source_value}
                else:
                    disks.append({'boot': False,
                                  'autoDelete': autoDelete,
                                  source_field: source_value})

        if num_roots > 1:
            log.warning('The launch config contains %d boot disks. Will '
                        'use the first one', num_roots)
        if image:
            if boot_disk:
                log.warning('A boot image is given while the launch config '
                            'contains a boot disk, too. The launch config '
                            'will be used.')
            else:
                if not isinstance(image, GCPMachineImage):
                    image = self.provider.compute.images.get(image)
                # Explicitly set diskName; otherwise, instance name will be
                # used by default which may conflict with existing disks.
                boot_disk = {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': image.id,
                        'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}

        if not boot_disk:
            log.warning('No boot disk is given for instance %s.', label)
            return None
        # The boot disk must be the first disk attached to the instance.
        disks.insert(0, boot_disk)

        config = {
            'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
            'machineType': vm_type.resource_url,
            'disks': disks,
            'networkInterfaces': [network_interface]
        }

        if vm_firewalls and isinstance(vm_firewalls, list):
            vm_firewall_names = []
            if isinstance(vm_firewalls[0], VMFirewall):
                vm_firewall_names = [f.name for f in vm_firewalls]
            elif isinstance(vm_firewalls[0], str):
                vm_firewall_names = vm_firewalls
            if len(vm_firewall_names) > 0:
                config['tags'] = {}
                config['tags']['items'] = vm_firewall_names

        if user_data:
            entry = {'key': 'user-data', 'value': user_data}
            config['metadata'] = {'items': [entry]}

        if key_pair:
            if not isinstance(key_pair, GCPKeyPair):
                key_pair = self._provider.security.key_pairs.get(key_pair)
            if key_pair:
                kp = key_pair._key_pair
                kp_entry = {
                    "key": "ssh-keys",
                    # Format is not removed from public key portion
                    "value": "{}:{} {}".format(
                        self.provider.vm_default_user_name,
                        kp.public_key,
                        kp.name)
                    }
                meta = config.get('metadata', {})
                if meta:
                    items = meta.get('items', [])
                    items.append(kp_entry)
                else:
                    config['metadata'] = {'items': [kp_entry]}

        config['labels'] = {'cblabel': label}

        operation = (self.provider
                         .gcp_compute.instances()
                         .insert(project=self.provider.project_name,
                                 zone=zone_name,
                                 body=config)
                         .execute())
        instance_id = operation.get('targetLink')
        self.provider.wait_for_operation(operation, zone=zone_name)
        cb_inst = self.get(instance_id)
        return cb_inst

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id):
        """
        Returns an instance given its name. Returns None
        if the object does not exist.

        A GCP instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        instance = self.provider.get_resource('instances', instance_id)
        return GCPInstance(self.provider, instance) if instance else None

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        """
        Searches for instances by instance label.
        :return: a list of Instance objects
        """
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        instances = [instance for instance in self.list()
                     if instance.label == label]
        return ClientPagedResultList(self.provider, instances,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.compute.instances.list",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        # For GCP API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .instances()
                        .list(project=self.provider.project_name,
                              zone=self.provider.zone_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        instances = [GCPInstance(self.provider, inst)
                     for inst in response.get('items', [])]
        if len(instances) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(instances))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=instances)

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance):
        instance = (instance if isinstance(instance, GCPInstance) else
                    self.get(instance))
        if instance:
            (self._provider
             .gcp_compute
             .instances()
             .delete(project=self.provider.project_name,
                     zone=instance.zone_name,
                     instance=instance.name)
             .execute())

    def create_launch_config(self):
        return GCPLaunchConfig(self.provider)


class GCPComputeService(BaseComputeService):
    # TODO: implement GCPComputeService
    def __init__(self, provider):
        super(GCPComputeService, self).__init__(provider)
        self._instance_svc = GCPInstanceService(self.provider)
        self._vm_type_svc = GCPVMTypeService(self.provider)
        self._region_svc = GCPRegionService(self.provider)
        self._images_svc = GCPImageService(self.provider)

    @property
    def images(self):
        return self._images_svc

    @property
    def vm_types(self):
        return self._vm_type_svc

    @property
    def instances(self):
        return self._instance_svc

    @property
    def regions(self):
        return self._region_svc


class GCPNetworkingService(BaseNetworkingService):

    def __init__(self, provider):
        super(GCPNetworkingService, self).__init__(provider)
        self._network_service = GCPNetworkService(self.provider)
        self._subnet_service = GCPSubnetService(self.provider)
        self._router_service = GCPRouterService(self.provider)
        self._gateway_service = GCPGatewayService(self.provider)
        self._floating_ip_service = GCPFloatingIPService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service

    @property
    def _gateways(self):
        return self._gateway_service

    @property
    def _floating_ips(self):
        return self._floating_ip_service


class GCPNetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(GCPNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id):
        network = self.provider.get_resource('networks', network_id)
        return GCPNetwork(self.provider, network) if network else None

    @dispatch(event="provider.networking.networks.find",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        """
        GCP networks are global. There is at most one network with a given
        name.
        """
        obj_list = self
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches),
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None, filter=None):
        # TODO: Decide whether we keep filter in 'list'
        networks = []
        response = (self.provider
                        .gcp_compute
                        .networks()
                        .list(project=self.provider.project_name,
                              filter=filter)
                        .execute())
        for network in response.get('items', []):
            networks.append(GCPNetwork(self.provider, network))
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label, cidr_block):
        """
        Creates an auto mode VPC network with default subnets. It is possible
        to add additional subnets later.
        """
        GCPNetwork.assert_valid_resource_label(label)
        name = GCPNetwork._generate_name_from_label(label, 'cbnet')
        body = {'name': name}
        # This results in a custom mode network
        body['autoCreateSubnetworks'] = False
        response = (self.provider
                        .gcp_compute
                        .networks()
                        .insert(project=self.provider.project_name,
                                body=body)
                        .execute())
        self.provider.wait_for_operation(response)
        cb_net = self.get(name)
        cb_net.label = label
        return cb_net

    def get_or_create_default(self):
        default_nets = self.provider.networking.networks.find(
            label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
        if default_nets:
            return default_nets[0]
        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.create(
                label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL,
                cidr_block=GCPNetwork.CB_DEFAULT_IPV4RANGE)

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network):
        # Accepts network object
        if isinstance(network, GCPNetwork):
            name = network.name
        # Accepts both name and ID
        elif 'googleapis' in network:
            name = network.split('/')[-1]
        else:
            name = network
        response = (self.provider
                        .gcp_compute
                        .networks()
                        .delete(project=self.provider.project_name,
                                network=name)
                        .execute())
        self.provider.wait_for_operation(response)
        # Remove label
        tag_name = "_".join(["network", name, "label"])
        if not helpers.remove_metadata_item(self.provider, tag_name):
            log.warning('No label was found associated with this network '
                        '"{}" when deleted.'.format(network))
        return True


class GCPRouterService(BaseRouterService):

    def __init__(self, provider):
        super(GCPRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id):
        router = self.provider.get_resource(
            'routers', router_id, region=self.provider.region_name)
        return GCPRouter(self.provider, router) if router else None

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        obj_list = self
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches),
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        region = self.provider.region_name
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .routers()
                        .list(project=self.provider.project_name,
                              region=region,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        routers = []
        for router in response.get('items', []):
            routers.append(GCPRouter(self.provider, router))
        if len(routers) > max_result:
            log.warning('Expected at most %d results; go %d',
                        max_result, len(routers))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=routers)

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network):
        log.debug("Creating GCP Router Service with params "
                  "[label: %s network: %s]", label, network)
        GCPRouter.assert_valid_resource_label(label)
        name = GCPRouter._generate_name_from_label(label, 'cb-router')

        if not isinstance(network, GCPNetwork):
            network = self.provider.networking.networks.get(network)
        network_url = network.resource_url
        region_name = self.provider.region_name
        response = (self.provider
                        .gcp_compute
                        .routers()
                        .insert(project=self.provider.project_name,
                                region=region_name,
                                body={'name': name,
                                      'network': network_url})
                        .execute())
        self.provider.wait_for_operation(response, region=region_name)
        cb_router = self.get(name)
        cb_router.label = label
        return cb_router

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router):
        r = router if isinstance(router, GCPRouter) else self.get(router)
        if r:
            (self.provider
             .gcp_compute
             .routers()
             .delete(project=self.provider.project_name,
                     region=r.region_name,
                     router=r.name)
             .execute())
            # Remove label
            tag_name = "_".join(["router", r.name, "label"])
            if not helpers.remove_metadata_item(self.provider, tag_name):
                log.warning('No label was found associated with this router '
                            '"{}" when deleted.'.format(r.name))

    def _get_in_region(self, router_id, region=None):
        region_name = self.provider.region_name
        if region:
            if not isinstance(region, GCPRegion):
                region = self.provider.compute.regions.get(region)
            region_name = region.name
        router = self.provider.get_resource(
            'routers', router_id, region=region_name)
        return GCPRouter(self.provider, router) if router else None


class GCPSubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(GCPSubnetService, self).__init__(provider)

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id):
        subnet = self.provider.get_resource('subnetworks', subnet_id)
        return GCPSubnet(self.provider, subnet) if subnet else None

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network=None, limit=None, marker=None):
        filter = None
        if network is not None:
            network = (network if isinstance(network, GCPNetwork)
                       else self.provider.networking.networks.get(network))
            filter = 'network eq %s' % network.resource_url
        region_name = self.provider.region_name
        subnets = []
        response = (self.provider
                        .gcp_compute
                        .subnetworks()
                        .list(project=self.provider.project_name,
                              region=region_name,
                              filter=filter)
                        .execute())
        for subnet in response.get('items', []):
            subnets.append(GCPSubnet(self.provider, subnet))
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label, network, cidr_block):
        """
        GCP subnets are regional. The default region, as set in the
        provider, is used.
        """
        GCPSubnet.assert_valid_resource_label(label)
        name = GCPSubnet._generate_name_from_label(label, 'cbsubnet')
        region_name = self.provider.region_name
#         for subnet in self.iter(network=network):
#            if BaseNetwork.cidr_blocks_overlap(subnet.cidr_block, cidr_block):
#                 if subnet.region_name != region_name:
#                     log.error('Failed to create subnetwork in region %s: '
#                                  'the given IP range %s overlaps with a '
#                                  'subnetwork in a different region %s',
#                                  region_name, cidr_block, subnet.region_name)
#                     return None
#                 return subnet
#             if subnet.label == label and subnet.region_name == region_name:
#                 return subnet

        body = {'ipCidrRange': cidr_block,
                'name': name,
                'network': network.resource_url,
                'region': region_name
                }
        response = (self.provider
                        .gcp_compute
                        .subnetworks()
                        .insert(project=self.provider.project_name,
                                region=region_name,
                                body=body)
                        .execute())
        self.provider.wait_for_operation(response, region=region_name)
        cb_subnet = self.get(name)
        cb_subnet.label = label
        return cb_subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet):
        sn = subnet if isinstance(subnet, GCPSubnet) else self.get(subnet)
        if not sn:
            return
        response = (self.provider
                    .gcp_compute
                    .subnetworks()
                    .delete(project=self.provider.project_name,
                            region=sn.region_name,
                            subnetwork=sn.name)
                    .execute())
        self.provider.wait_for_operation(response, region=sn.region_name)
        # Remove label
        tag_name = "_".join(["subnet", sn.name, "label"])
        if not helpers.remove_metadata_item(self._provider, tag_name):
            log.warning('No label was found associated with this subnet '
                        '"{}" when deleted.'.format(sn.name))

    def get_or_create_default(self):
        """
        Return an existing or create a new subnet in the provider default zone.

        In GCP, subnets are a regional resource so a single subnet can services
        an entire region.
        """
        region_name = self.provider.region_name
        # Check if a default subnet already exists for the given region/zone
        for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
            if sn.region_name == region_name:
                return sn
        # No default subnet in the current zone. Look for a default network,
        # then create a subnet whose address space does not overlap with any
        # other existing subnets. If there are existing subnets, this process
        # largely assumes the subnet address spaces are contiguous when it
        # does the calculations (e.g., 10.0.0.0/24, 10.0.1.0/24).
        cidr_block = GCPSubnet.CB_DEFAULT_SUBNET_IPV4RANGE
        net = self.provider.networking.networks.get_or_create_default()
        if net.subnets:
            max_sn = net.subnets[0]
            # Find the maximum address subnet address space within the network
            for esn in net.subnets:
                if (ipaddress.ip_network(esn.cidr_block) >
                        ipaddress.ip_network(max_sn.cidr_block)):
                    max_sn = esn
            max_sn_ipa = ipaddress.ip_network(max_sn.cidr_block)
            # Find the next available subnet after the max one, based on the
            # max subnet size
            next_sn_address = (
                next(max_sn_ipa.hosts()) + max_sn_ipa.num_addresses - 1)
            cidr_block = "{}/{}".format(next_sn_address, max_sn_ipa.prefixlen)
        sn = self.provider.networking.subnets.create(
                label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL,
                cidr_block=cidr_block, network=net)
        router = self.provider.networking.routers.get_or_create_default(net)
        router.attach_subnet(sn)
        gateway = net.gateways.get_or_create()
        router.attach_gateway(gateway)
        return sn


class GCPStorageService(BaseStorageService):

    def __init__(self, provider):
        super(GCPStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = GCPVolumeService(self.provider)
        self._snapshot_svc = GCPSnapshotService(self.provider)
        self._bucket_svc = GCPBucketService(self.provider)
        self._bucket_obj_svc = GCPBucketObjectService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc

    @property
    def _bucket_objects(self):
        return self._bucket_obj_svc


class GCPVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(GCPVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id):
        vol = self.provider.get_resource('disks', volume_id)
        return GCPVolume(self.provider, vol) if vol else None

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        """
        Searches for a volume by a given list of attributes.
        """
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        filtr = 'labels.cblabel eq ' + label
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.zone_name,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        gcp_vols = [GCPVolume(self.provider, vol)
                    for vol in response.get('items', [])]
        if len(gcp_vols) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(gcp_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gcp_vols)

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        """
        List all volumes.

        limit: The maximum number of volumes to return. The returned
               ResultList's is_truncated property can be used to determine
               whether more records are available.
        """
        # For GCP API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.zone_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        gcp_vols = [GCPVolume(self.provider, vol)
                    for vol in response.get('items', [])]
        if len(gcp_vols) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(gcp_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gcp_vols)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label, size, snapshot=None, description=None):
        GCPVolume.assert_valid_resource_label(label)
        name = GCPVolume._generate_name_from_label(label, 'cb-vol')
        zone_name = self.provider.zone_name
        snapshot_id = snapshot.id if isinstance(
            snapshot, GCPSnapshot) and snapshot else snapshot
        labels = {'cblabel': label}
        if description:
            labels['description'] = description
        disk_body = {
            'name': name,
            'sizeGb': size,
            'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
            'sourceSnapshot': snapshot_id,
            'labels': labels
        }
        operation = (self.provider
                         .gcp_compute
                         .disks()
                         .insert(
                             project=self._provider.project_name,
                             zone=zone_name,
                             body=disk_body)
                         .execute())
        cb_vol = self.get(operation.get('targetLink'))
        return cb_vol

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume):
        volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
        if volume:
            (self._provider.gcp_compute
                           .disks()
                           .delete(project=self.provider.project_name,
                                   zone=volume.zone_name,
                                   disk=volume.name)
                           .execute())


class GCPSnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(GCPSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id):
        snapshot = self.provider.get_resource('snapshots', snapshot_id)
        return GCPSnapshot(self.provider, snapshot) if snapshot else None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        filtr = 'labels.cblabel eq ' + label
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        snapshots = [GCPSnapshot(self.provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        snapshots = [GCPSnapshot(self.provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label, volume, description=None):
        GCPSnapshot.assert_valid_resource_label(label)
        name = GCPSnapshot._generate_name_from_label(label, 'cbsnap')
        volume_name = volume.name if isinstance(volume, GCPVolume) else volume
        labels = {'cblabel': label}
        if description:
            labels['description'] = description
        snapshot_body = {
            "name": name,
            "labels": labels
        }
        operation = (self.provider
                         .gcp_compute
                         .disks()
                         .createSnapshot(
                             project=self.provider.project_name,
                             zone=self.provider.zone_name,
                             disk=volume_name, body=snapshot_body)
                         .execute())
        if 'zone' not in operation:
            return None
        self.provider.wait_for_operation(operation,
                                         zone=self.provider.zone_name)
        cb_snap = self.get(name)
        return cb_snap

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot):
        snapshot = (snapshot if isinstance(snapshot, GCPSnapshot)
                    else self.get(snapshot))
        if snapshot:
            (self.provider
                 .gcp_compute
                 .snapshots()
                 .delete(project=self.provider.project_name,
                         snapshot=snapshot.name)
                 .execute())


class GCPBucketService(BaseBucketService):

    def __init__(self, provider):
        super(GCPBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist or if the user does not have permission to access the
        bucket.
        """
        bucket = self.provider.get_resource('buckets', bucket_id)
        return GCPBucket(self.provider, bucket) if bucket else None

    @dispatch(event="provider.storage.buckets.find",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def find(self, limit=None, marker=None, **kwargs):
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))

        buckets = [bucket for bucket in self if name in bucket.name]
        return ClientPagedResultList(self.provider, buckets, limit=limit,
                                     marker=marker)

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_storage
                        .buckets()
                        .list(project=self.provider.project_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        buckets = []
        for bucket in response.get('items', []):
            buckets.append(GCPBucket(self.provider, bucket))
        if len(buckets) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(buckets))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=buckets)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name, location=None):
        GCPBucket.assert_valid_resource_name(name)
        body = {'name': name}
        if location:
            body['location'] = location
        try:
            response = (self.provider
                            .gcp_storage
                            .buckets()
                            .insert(project=self.provider.project_name,
                                    body=body)
                            .execute())
            # GCP has a rate limit of 1 operation per 2 seconds for bucket
            # creation/deletion: https://cloud.google.com/storage/quotas.
            # Throttle here to avoid future failures.
            time.sleep(2)
            return GCPBucket(self.provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # 409 = conflict
            if http_error.resp.status in [409]:
                raise DuplicateResourceException(
                    'Bucket already exists with name {0}'.format(name))
            else:
                raise

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket):
        """
        Delete this bucket.
        """
        b = bucket if isinstance(bucket, GCPBucket) else self.get(bucket)
        if b:
            (self.provider
                 .gcp_storage
                 .buckets()
                 .delete(bucket=b.name)
                 .execute())
            # GCP has a rate limit of 1 operation per 2 seconds for bucket
            # creation/deletion: https://cloud.google.com/storage/quotas.
            # Throttle here to avoid future failures.
            time.sleep(2)


class GCPBucketObjectService(BaseBucketObjectService):

    def __init__(self, provider):
        super(GCPBucketObjectService, self).__init__(provider)

    def get(self, bucket, name):
        """
        Retrieve a given object from this bucket.
        """
        obj = self.provider.get_resource('objects', name,
                                         bucket=bucket.name)
        return GCPBucketObject(self.provider, bucket, obj) if obj else None

    def list(self, bucket, limit=None, marker=None, prefix=None):
        """
        List all objects within this bucket.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_storage
                        .objects()
                        .list(bucket=bucket.name,
                              prefix=prefix if prefix else '',
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        objects = []
        for obj in response.get('items', []):
            objects.append(GCPBucketObject(self.provider, bucket, obj))
        if len(objects) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(objects))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=objects)

    def find(self, bucket, limit=None, marker=None, **kwargs):
        filters = ['name']
        matches = cb_helpers.generic_find(filters, kwargs, bucket.objects)
        return ClientPagedResultList(self._provider, list(matches),
                                     limit=limit, marker=marker)

    def _create_object_with_media_body(self, bucket, name, media_body):
        response = (self.provider
                    .gcp_storage
                    .objects()
                    .insert(bucket=bucket.name,
                            body={'name': name},
                            media_body=media_body)
                    .execute())
        return response

    def create(self, bucket, name):
        response = self._create_object_with_media_body(
                            bucket,
                            name,
                            googleapiclient.http.MediaIoBaseUpload(
                                io.BytesIO(b''), mimetype='plain/text'))
        return GCPBucketObject(self._provider,
                               bucket,
                               response) if response else None


class GCPGatewayService(BaseGatewayService):
    _DEFAULT_GATEWAY_NAME = 'default-internet-gateway'
    _GATEWAY_URL_PREFIX = 'global/gateways/'

    def __init__(self, provider):
        super(GCPGatewayService, self).__init__(provider)
        self._default_internet_gateway = GCPInternetGateway(
            provider,
            {'id': (GCPGatewayService._GATEWAY_URL_PREFIX +
                    GCPGatewayService._DEFAULT_GATEWAY_NAME),
             'name': GCPGatewayService._DEFAULT_GATEWAY_NAME})

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network):
        return self._default_internet_gateway

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network, gateway):
        pass

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network, limit=None, marker=None):
        gws = [self._default_internet_gateway]
        return ClientPagedResultList(self._provider,
                                     gws,
                                     limit=limit, marker=marker)


class GCPFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider):
        super(GCPFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway, floating_ip_id):
        fip = self.provider.get_resource('addresses', floating_ip_id)
        return (GCPFloatingIP(self.provider, fip)
                if fip else None)

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gcp_compute
                        .addresses()
                        .list(project=self.provider.project_name,
                              region=self.provider.region_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        ips = [GCPFloatingIP(self.provider, ip)
               for ip in response.get('items', [])]
        if len(ips) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(ips))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=ips)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway):
        region_name = self.provider.region_name
        ip_name = 'ip-{0}'.format(uuid.uuid4())
        response = (self.provider
                    .gcp_compute
                    .addresses()
                    .insert(project=self.provider.project_name,
                            region=region_name,
                            body={'name': ip_name})
                    .execute())
        self.provider.wait_for_operation(response, region=region_name)
        return self.get(gateway, ip_name)

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway, fip):
        fip = (fip if isinstance(fip, GCPFloatingIP)
               else self.get(gateway, fip))
        project_name = self.provider.project_name
        # First, delete the forwarding rule, if there is any.
        # pylint:disable=protected-access
        if fip._rule:
            response = (self.provider
                        .gcp_compute
                        .forwardingRules()
                        .delete(project=project_name,
                                region=fip.region_name,
                                forwardingRule=fip._rule['name'])
                        .execute())
            self.provider.wait_for_operation(response,
                                             region=fip.region_name)

        # Release the address.
        response = (self.provider
                    .gcp_compute
                    .addresses()
                    .delete(project=project_name,
                            region=fip.region_name,
                            address=fip._ip['name'])
                    .execute())
        self.provider.wait_for_operation(response,
                                         region=fip.region_name)
