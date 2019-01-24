import hashlib
import logging
import time
import uuid
from collections import namedtuple

import googleapiclient

import cloudbridge as cb
from cloudbridge.cloud.base import helpers as cb_helpers
from cloudbridge.cloud.base.resources import ClientPagedResultList
from cloudbridge.cloud.base.resources import ServerPagedResultList
from cloudbridge.cloud.base.services import BaseBucketService
from cloudbridge.cloud.base.services import BaseComputeService
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
from cloudbridge.cloud.base.services import BaseVMFirewallService
from cloudbridge.cloud.base.services import BaseVMTypeService
from cloudbridge.cloud.base.services import BaseVolumeService
from cloudbridge.cloud.interfaces.exceptions import DuplicateResourceException
from cloudbridge.cloud.interfaces.resources import TrafficDirection
from cloudbridge.cloud.interfaces.resources import VMFirewall
from cloudbridge.cloud.providers.gce import helpers

from .resources import GCEFirewallsDelegate
from .resources import GCEInstance
from .resources import GCEKeyPair
from .resources import GCELaunchConfig
from .resources import GCEMachineImage
from .resources import GCENetwork
from .resources import GCEPlacementZone
from .resources import GCERegion
from .resources import GCERouter
from .resources import GCESnapshot
from .resources import GCESubnet
from .resources import GCEVMFirewall
from .resources import GCEVMType
from .resources import GCEVolume
from .resources import GCSBucket

log = logging.getLogger(__name__)


class GCESecurityService(BaseSecurityService):

    def __init__(self, provider):
        super(GCESecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = GCEKeyPairService(provider)
        self._vm_firewalls = GCEVMFirewallService(provider)

    @property
    def key_pairs(self):
        return self._key_pairs

    @property
    def vm_firewalls(self):
        return self._vm_firewalls


class GCEKeyPairService(BaseKeyPairService):

    GCEKeyInfo = namedtuple('GCEKeyInfo', 'format public_key email')

    def __init__(self, provider):
        super(GCEKeyPairService, self).__init__(provider)

    def _iter_gce_key_pairs(self, provider):
        """
        Iterates through the project's metadata, yielding a GCEKeyInfo object
        for each entry in commonInstanceMetaData/items
        """
        metadata = helpers.get_common_metadata(provider)
        for kpinfo in self._iter_gce_ssh_keys(metadata):
            yield kpinfo

    def _get_or_add_sshkey_entry(self, metadata):
        """
        Get the ssh-keys entry from commonInstanceMetadata/items.
        If an entry does not exist, adds a new empty entry
        """
        sshkey_entry = None
        entries = [item for item in metadata.get('items', [])
                   if item['key'] == 'ssh-keys']
        if entries:
            sshkey_entry = entries[0]
        else:  # add a new entry
            sshkey_entry = {'key': 'ssh-keys', 'value': ''}
            if 'items' not in metadata:
                metadata['items'] = [sshkey_entry]
            else:
                metadata['items'].append(sshkey_entry)
        return sshkey_entry

    def _iter_gce_ssh_keys(self, metadata):
        """
        Iterates through the ssh keys given a commonInstanceMetadata dict,
        yielding a GCEKeyInfo object for each entry in
        commonInstanceMetaData/items
        """
        sshkeys = self._get_or_add_sshkey_entry(metadata)["value"]
        for key in sshkeys.split("\n"):
            # elems should be "ssh-rsa <public_key> <email>"
            elems = key.split(" ")
            if elems and elems[0]:  # ignore blank lines
                yield GCEKeyPairService.GCEKeyInfo(
                        elems[0], elems[1], elems[2])

    def update_kps_in_metadata(self, provider, callback):
        def _process_kps_from_metadata(metadata):
            # add a new entry if one doesn't exist
            sshkey_entry = self._get_or_add_sshkey_entry(metadata)
            gce_kp_list = callback(self._iter_gce_ssh_keys(metadata))

            entry = ""
            for gce_kp in gce_kp_list:
                entry = entry + u"{0} {1} {2}\n".format(gce_kp.format,
                                                        gce_kp.public_key,
                                                        gce_kp.email)
            sshkey_entry["value"] = entry.rstrip()

        helpers.gce_metadata_save_op(provider, _process_kps_from_metadata)

    def gce_kp_to_id(self, gce_kp):
        """
        Accept a GCEKeyInfo object and return a unique
        ID for it
        """
        md5 = hashlib.md5()
        md5.update(gce_kp.public_key.encode())
        return md5.hexdigest()

    def get(self, key_pair_id):
        """
        Returns a KeyPair given its ID.
        """
        for kp in self:
            if kp.id == key_pair_id:
                return kp
        else:
            return None

    def list(self, limit=None, marker=None):
        key_pairs = []
        for gce_kp in self._iter_gce_key_pairs(self.provider):
            kp_id = self.gce_kp_to_id(gce_kp)
            key_pairs.append(GCEKeyPair(self.provider, kp_id, gce_kp.email))
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    def find(self, **kwargs):
        """
        Searches for a key pair by a given list of attributes.
        """
        kp_name = kwargs.get('name', None)
        kp_id = kwargs.get('id', None)
        for parameter in kwargs:
            if parameter not in ('id', 'name'):
                cb.log.error('Unrecognised parameters for search: %s. '
                             'Supported attributes: id, name', parameter)

        out = []
        for kp in self:
            if kp_name is not None and kp.name != kp_name:
                continue
            if kp_id is not None and kp.id != kp_id:
                continue
            out.append(kp)
        return out

    def create(self, name, public_key_material=None):
        GCEKeyPair.assert_valid_resource_name(name)

        if self.find(name=name):
            raise DuplicateResourceException(
                'A KeyPair with the same name %s exists', name)
        private_key = None
        if not public_key_material:
            private_key, public_key_material = helpers.generate_key_pair()
        parts = public_key_material.split(' ')
        if len(parts) == 2:
            public_key_material = parts[1]
        kp_info = GCEKeyPairService.GCEKeyInfo(
            '%s:ssh-rsa' % name, public_key_material, name)

        def _add_kp(gce_kp_generator):
            kp_list = []
            # Add the new key pair
            kp_list.append(kp_info)
            for gce_kp in gce_kp_generator:
                kp_list.append(gce_kp)
            return kp_list

        self.update_kps_in_metadata(self.provider, _add_kp)
        return GCEKeyPair(self.provider, self.gce_kp_to_id(kp_info), name,
                          private_key)

    def delete(self, key_pair_id):

        def _delete_key(gce_kp_generator):
            kp_list = []
            for gce_kp in gce_kp_generator:
                if self.gce_kp_to_id(gce_kp) == key_pair_id:
                    continue
                else:
                    kp_list.append(gce_kp)
            return kp_list

        self.update_kps_in_metadata(self.provider, _delete_key)


class GCEVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider):
        super(GCEVMFirewallService, self).__init__(provider)
        self._delegate = GCEFirewallsDelegate(provider)

    def get(self, group_id):
        tag, network_name = self._delegate.get_tag_network_from_id(group_id)
        if tag is None:
            return None
        network = self.provider.networking.networks.get_by_name(network_name)
        return GCEVMFirewall(self._delegate, tag, network)

    def list(self, limit=None, marker=None):
        vm_firewalls = []
        for tag, network_name in self._delegate.tag_networks:
            network = self.provider.networking.networks.get_by_name(
                    network_name)
            vm_firewall = GCEVMFirewall(self._delegate, tag, network)
            vm_firewalls.append(vm_firewall)
        return ClientPagedResultList(self.provider, vm_firewalls,
                                     limit=limit, marker=marker)

    def create(self, label, description, network=None):
        GCEVMFirewall.assert_valid_resource_label(label)
        network = (network if isinstance(network, GCENetwork)
                   else self.provider.networking.networks.get(network))
        fw = GCEVMFirewall(self._delegate, label, network, description)
        # This rule exists implicitly. Add it explicitly so that the firewall
        # is not empty and the rule is shown by list/get/find methods.
        fw.rules.create_with_priority(
                direction=TrafficDirection.OUTBOUND, protocol='tcp',
                priority=65534, cidr='0.0.0.0/0')
        fw.label = label
        return fw

    def delete(self, group_id):
        return self._delegate.delete_tag_network_with_id(group_id)

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
            network = self.provider.networking.networks.get_by_name(net_name)
            vm_firewalls.append(
                GCEVMFirewall(self._delegate, tag, network))
        return vm_firewalls


class GCEVMTypeService(BaseVMTypeService):

    def __init__(self, provider):
        super(GCEVMTypeService, self).__init__(provider)

    @property
    def instance_data(self):
        response = (self.provider
                        .gce_compute
                        .machineTypes()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone)
                        .execute())
        return response['items']

    def get(self, vm_type_id):
        vm_type = self.provider.get_resource('machineTypes', vm_type_id)
        return GCEVMType(self.provider, vm_type) if vm_type else None

    def find(self, **kwargs):
        matched_inst_types = []
        for inst_type in self.instance_data:
            is_match = True
            for key, value in kwargs.iteritems():
                if key not in inst_type:
                    raise TypeError("The attribute key is not valid.")
                if inst_type.get(key) != value:
                    is_match = False
                    break
            if is_match:
                matched_inst_types.append(
                    GCEVMType(self.provider, inst_type))
        return matched_inst_types

    def list(self, limit=None, marker=None):
        inst_types = [GCEVMType(self.provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class GCERegionService(BaseRegionService):

    def __init__(self, provider):
        super(GCERegionService, self).__init__(provider)

    def get(self, region_id):
        region = self.provider.get_resource('regions', region_id,
                                            region=region_id)
        return GCERegion(self.provider, region) if region else None

    def list(self, limit=None, marker=None):
        max_result = limit if limit is not None and limit < 500 else 500
        regions_response = (self.provider
                                .gce_compute
                                .regions()
                                .list(project=self.provider.project_name,
                                      maxResults=max_result,
                                      pageToken=marker)
                                .execute())
        regions = [GCERegion(self.provider, region)
                   for region in regions_response['items']]
        if len(regions) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(regions))
        return ServerPagedResultList('nextPageToken' in regions_response,
                                     regions_response.get('nextPageToken'),
                                     False, data=regions)

    @property
    def current(self):
        return self.get(self.provider.region_name)


class GCEImageService(BaseImageService):

    def __init__(self, provider):
        super(GCEImageService, self).__init__(provider)
        self._public_images = None

    _PUBLIC_IMAGE_PROJECTS = ['centos-cloud', 'coreos-cloud', 'debian-cloud',
                              'opensuse-cloud', 'ubuntu-os-cloud']

    def _retrieve_public_images(self):
        if self._public_images is not None:
            return
        self._public_images = []
        try:
            for project in GCEImageService._PUBLIC_IMAGE_PROJECTS:
                for image in helpers.iter_all(
                        self.provider.gce_compute.images(), project=project):
                    self._public_images.append(
                        GCEMachineImage(self.provider, image))
        except googleapiclient.errors.HttpError as http_error:
                cb.log.warning("googleapiclient.errors.HttpError: {0}".format(
                    http_error))

    def get(self, image_id):
        """
        Returns an Image given its id
        """
        image = self.provider.get_resource('images', image_id)
        if image:
            return GCEMachineImage(self.provider, image)
        self._retrieve_public_images()
        for public_image in self._public_images:
            if public_image.id == image_id or public_image.name == image_id:
                return public_image
        return None

    def find(self, label, limit=None, marker=None):
        """
        Searches for an image by a given list of attributes
        """
        filters = {'label': label}
        # Retrieve all available images by setting limit to sys.maxsize
        images = [image for image in self if image.label == filters['label']]
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all images.
        """
        self._retrieve_public_images()
        images = []
        if (self.provider.project_name not in
                GCEImageService._PUBLIC_IMAGE_PROJECTS):
            try:
                for image in helpers.iter_all(
                        self.provider.gce_compute.images(),
                        project=self.provider.project_name):
                    images.append(GCEMachineImage(self.provider, image))
            except googleapiclient.errors.HttpError as http_error:
                cb.log.warning(
                    "googleapiclient.errors.HttpError: {0}".format(http_error))
        images.extend(self._public_images)
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class GCEInstanceService(BaseInstanceService):

    def __init__(self, provider):
        super(GCEInstanceService, self).__init__(provider)

    def create(self, label, image, vm_type, subnet, zone=None,
               key_pair=None, vm_firewalls=None, user_data=None,
               launch_config=None, **kwargs):
        """
        Creates a new virtual machine instance.
        """
        GCEInstance.assert_valid_resource_name(label)
        zone_name = self.provider.default_zone
        if zone:
            if not isinstance(zone, GCEPlacementZone):
                zone = GCEPlacementZone(
                    self.provider,
                    self.provider.get_resource('zones', zone, zone=zone))
            zone_name = zone.name
        if not isinstance(vm_type, GCEVMType):
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
        if isinstance(launch_config, GCELaunchConfig):
            for disk in launch_config.block_devices:
                if not disk.source:
                    volume_name = 'disk-{0}'.format(uuid.uuid4())
                    volume_size = disk.size if disk.size else 1
                    volume = self.provider.storage.volumes.create(
                        volume_name, volume_size, zone)
                    volume.wait_till_ready()
                    source_field = 'source'
                    source_value = volume.id
                elif isinstance(disk.source, GCEMachineImage):
                    source_field = 'initializeParams'
                    # Explicitly set diskName; otherwise, instance label will
                    # be used by default which may collide with existing disks.
                    source_value = {
                        'sourceImage': disk.source.id,
                        'diskName': 'image-disk-{0}'.format(uuid.uuid4())}
                elif isinstance(disk.source, GCEVolume):
                    source_field = 'source'
                    source_value = disk.source.id
                elif isinstance(disk.source, GCESnapshot):
                    volume = disk.source.create_volume(zone, size=disk.size)
                    volume.wait_till_ready()
                    source_field = 'source'
                    source_value = volume.id
                else:
                    cb.log.warning('Unknown disk source')
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
            cb.log.warning('The launch config contains %d boot disks. Will '
                           'use the first one', num_roots)
        if image:
            if boot_disk:
                cb.log.warning('A boot image is given while the launch config '
                               'contains a boot disk, too. The launch config '
                               'will be used.')
            else:
                if not isinstance(image, GCEMachineImage):
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
            cb.log.warning('No boot disk is given for instance %s.', label)
            return None
        # The boot disk must be the first disk attached to the instance.
        disks.insert(0, boot_disk)

        config = {
            'name': GCEInstance._generate_name_from_label(label, 'cb-inst'),
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
        try:
            operation = (self.provider
                             .gce_compute.instances()
                             .insert(project=self.provider.project_name,
                                     zone=zone_name,
                                     body=config)
                             .execute())
        except googleapiclient.errors.HttpError as http_error:
            # If the operation request fails, the API will raise
            # googleapiclient.errors.HttpError.
            cb.log.warning(
                "googleapiclient.errors.HttpError: {0}".format(http_error))
            return None
        instance_id = operation.get('targetLink')
        self.provider.wait_for_operation(operation, zone=zone_name)
        cb_inst = self.get(instance_id)
        cb_inst.label = label
        if key_pair:
            cb_inst.key_pair_id = key_pair
        return cb_inst

    def get(self, instance_id):
        """
        Returns an instance given its name. Returns None
        if the object does not exist.

        A GCE instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        instance = self.provider.get_resource('instances', instance_id)
        return GCEInstance(self.provider, instance) if instance else None

    def find(self, label, limit=None, marker=None):
        """
        Searches for instances by instance label.
        :return: a list of Instance objects
        """
        instances = [instance for instance in self.list()
                     if instance.label == label]
        if limit and len(instances) > limit:
            instances = instances[:limit]
        return instances

    def list(self, limit=None, marker=None):
        """
        List all instances.
        """
        # For GCE API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .instances()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        instances = [GCEInstance(self.provider, inst)
                     for inst in response.get('items', [])]
        if len(instances) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(instances))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=instances)

    def create_launch_config(self):
        return GCELaunchConfig(self.provider)


class GCEComputeService(BaseComputeService):
    # TODO: implement GCEComputeService
    def __init__(self, provider):
        super(GCEComputeService, self).__init__(provider)
        self._instance_svc = GCEInstanceService(self.provider)
        self._vm_type_svc = GCEVMTypeService(self.provider)
        self._region_svc = GCERegionService(self.provider)
        self._images_svc = GCEImageService(self.provider)

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


class GCENetworkingService(BaseNetworkingService):

    def __init__(self, provider):
        super(GCENetworkingService, self).__init__(provider)
        self._network_service = GCENetworkService(self.provider)
        self._subnet_service = GCESubnetService(self.provider)
        self._router_service = GCERouterService(self.provider)

    @property
    def networks(self):
        return self._network_service

    @property
    def subnets(self):
        return self._subnet_service

    @property
    def routers(self):
        return self._router_service


class GCENetworkService(BaseNetworkService):

    def __init__(self, provider):
        super(GCENetworkService, self).__init__(provider)

    def get(self, network_id):
        network = self.provider.get_resource('networks', network_id)
        return GCENetwork(self.provider, network) if network else None

    def find(self, limit=None, marker=None, **kwargs):
        """
        GCE networks are global. There is at most one network with a given
        name.
        """
        obj_list = self
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def get_by_name(self, network_name):
        # Get already works with name
        # TODO: Decide if we neet to keep this function altogether/add it
        # everywhere?
        if network_name:
            return self.get(network_name)
        else:
            return None

    def list(self, limit=None, marker=None, filter=None):
        # TODO: Decide whether we keep filter in 'list'
        networks = []
        try:
            response = (self.provider
                            .gce_compute
                            .networks()
                            .list(project=self.provider.project_name,
                                  filter=filter)
                            .execute())
            for network in response.get('items', []):
                networks.append(GCENetwork(self.provider, network))
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    def _create(self, label, cidr_block, create_subnetworks):
        """
        Possible values for 'create_subnetworks' are:

        None: For creating a legacy (non-subnetted) network.
        True: For creating an auto mode VPC network. This also creates a
              subnetwork in every region.
        False: For creating a custom mode VPC network. Subnetworks should be
               created manually.
        """
        GCENetwork.assert_valid_resource_label(label)
        if create_subnetworks is not None and cidr_block is not None:
            cb.log.warning('cidr_block is ignored in non-legacy networks. '
                           'Auto mode networks use the default CIDR of '
                           '%s. For custom networks, you should create subnets'
                           'in each region with explicit CIDR blocks',
                           GCENetwork.CB_DEFAULT_IPV4RANGE)
            cidr_block = None
        name = GCENetwork._generate_name_from_label(label, 'cbnet')
        body = {'name': name}
        if cidr_block:
            body['IPv4Range'] = cidr_block
        else:
            body['autoCreateSubnetworks'] = create_subnetworks
        try:
            response = (self.provider
                            .gce_compute
                            .networks()
                            .insert(project=self.provider.project_name,
                                    body=body)
                            .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_operation(response)
            return self.get(name)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None

    def create(self, label, cidr_block):
        """
        Creates an auto mode VPC network with default subnets. It is possible
        to add additional subnets later.
        """
        cb_net = self._create(label, cidr_block, False)
        cb_net.label = label
        return cb_net

    def get_or_create_default(self):
        return self._create(GCEFirewallsDelegate.DEFAULT_NETWORK, None, True)

    def delete(self, network):
        # Accepts network object
        if isinstance(network, GCENetwork):
            name = network.name
        # Accepts both name and ID
        elif 'googleapis' in network:
            name = network.split('/')[-1]
        else:
            name = network
        try:
            response = (self.provider
                            .gce_compute
                            .networks()
                            .delete(project=self.provider.project_name,
                                    network=name)
                            .execute())
            if 'error' in response:
                return False
            self.provider.wait_for_operation(response)
            # Remove label
            tag_name = "_".join(["network", name, "label"])
            if not helpers.remove_metadata_item(self.provider, tag_name):
                log.warning('No label was found associated with this network '
                            '"{}" when deleted.'.format(network.name))
        except googleapiclient.errors.HttpError as http_error:
            log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return False
        return True


class GCERouterService(BaseRouterService):

    def __init__(self, provider):
        super(GCERouterService, self).__init__(provider)

    def get(self, router_id):
        return self._get_in_region(router_id)

    def find(self, **kwargs):
        obj_list = self
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(self._provider, list(matches))

    def list(self, limit=None, marker=None):
        region = self.provider.region_name
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .routers()
                        .list(project=self.provider.project_name,
                              region=region,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        routers = []
        for router in response.get('items', []):
            routers.append(GCERouter(self.provider, router))
        if len(routers) > max_result:
            cb.log.warning('Expected at most %d results; go %d',
                           max_result, len(routers))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=routers)

    def create(self, label, network):
        log.debug("Creating GCE Router Service with params "
                  "[label: %s network: %s]", label, network)
        GCERouter.assert_valid_resource_label(label)
        name = GCERouter._generate_name_from_label(label, 'cb-router')

        if not isinstance(network, GCENetwork):
            network = self.provider.networking.networks.get(network)
        network_url = network.resource_url
        region_name = self.provider.region_name
        try:
            response = (self.provider
                            .gce_compute
                            .routers()
                            .insert(project=self.provider.project_name,
                                    region=region_name,
                                    body={'name': name,
                                          'network': network_url,
                                          'description': label})
                            .execute())
            if 'error' in response:
                return None
            self.provider.wait_for_operation(response, region=region_name)
            return self._get_in_region(name, region_name)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None

    def delete(self, router):
        region_name = self.provider.region_name
        name = router.name if isinstance(router, GCERouter) else router
        response = (self.provider
                        .gce_compute
                        .routers()
                        .delete(project=self.provider.project_name,
                                region=region_name,
                                router=name)
                        .execute())
        self._provider.wait_for_operation(response, region=region_name)

    def _get_in_region(self, router_id, region=None):
        region_name = self.provider.region_name
        if region:
            if not isinstance(region, GCERegion):
                region = self.provider.compute.regions.get(region)
            region_name = region.name
        router = self.provider.get_resource(
            'routers', router_id, region=region_name)
        return GCERouter(self.provider, router) if router else None


class GCESubnetService(BaseSubnetService):

    def __init__(self, provider):
        super(GCESubnetService, self).__init__(provider)

    def get(self, subnet_id):
        subnet = self.provider.get_resource('subnetworks', subnet_id)
        return GCESubnet(self.provider, subnet) if subnet else None

    def list(self, network=None, zone=None, limit=None, marker=None):
        """
        If the zone is not given, we list all subnetworks, in all regions.
        """
        filter = None
        if network is not None:
            network = (network if isinstance(network, GCENetwork)
                       else self.provider.networking.networks.get(network))
            filter = 'network eq %s' % network.resource_url
        region_names = []
        if zone:
            region_names.append(self._zone_to_region_name(zone))
        else:
            for r in self.provider.compute.regions.list():
                region_names.append(r.name)
        subnets = []
        for region_name in region_names:
            response = (self.provider
                            .gce_compute
                            .subnetworks()
                            .list(project=self.provider.project_name,
                                  region=region_name,
                                  filter=filter)
                            .execute())
            for subnet in response.get('items', []):
                subnets.append(GCESubnet(self.provider, subnet))
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    def create(self, label, network, cidr_block, zone):
        """
        GCE subnets are regional. The region is inferred from the zone;
        otherwise, the default region, as set in the
        provider, is used.

        If a subnet with overlapping IP range exists already, we return that
        instead of creating a new subnet. In this case, other parameters, i.e.
        the name and the zone, are ignored.
        """
        GCESubnet.assert_valid_resource_label(label)
        name = GCESubnet._generate_name_from_label(label, 'cbsubnet')
        region_name = self._zone_to_region_name(zone)
#         for subnet in self.iter(network=network):
#            if BaseNetwork.cidr_blocks_overlap(subnet.cidr_block, cidr_block):
#                 if subnet.region_name != region_name:
#                     cb.log.error('Failed to create subnetwork in region %s: '
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
        try:
            response = (self.provider
                            .gce_compute
                            .subnetworks()
                            .insert(project=self.provider.project_name,
                                    region=region_name,
                                    body=body)
                            .execute())
            if 'error' in response:
                cb.log.warning('Error while creating a subnet: %s',
                               response['error'])
                return None
            self.provider.wait_for_operation(response, region=region_name)
            cb_subnet = self.get(name)
            cb_subnet.label = label
            return cb_subnet
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None

    def get_or_create_default(self, zone=None):
        """
        Every GCP project comes with a default auto mode VPC network. An auto
        mode VPC network has exactly one subnetwork per region. This method
        returns the subnetwork of the default network that spans the given
        zone.
        """
        network = self.provider.networking.networks.get_or_create_default()
        subnets = list(self.iter(network=network, zone=zone))
        if len(subnets) > 1:
            cb.log.warning('The default network has more than one subnetwork '
                           'in a region')
        if len(subnets) > 0:
            return subnets[0]
        cb.log.warning('The default network has no subnetwork in a region')
        return None

    def delete(self, subnet):
        try:
            response = (self.provider
                            .gce_compute
                            .subnetworks()
                            .delete(project=self.provider.project_name,
                                    region=subnet.region_name,
                                    subnetwork=subnet.name)
                            .execute())
            self._provider.wait_for_operation(
                response, region=subnet.region_name)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)

    def _zone_to_region_name(self, zone):
        if zone:
            if not isinstance(zone, GCEPlacementZone):
                zone = GCEPlacementZone(
                    self.provider,
                    self.provider.get_resource('zones', zone, zone=zone))
            return zone.region_name
        return self.provider.region_name


class GCPStorageService(BaseStorageService):

    def __init__(self, provider):
        super(GCPStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = GCEVolumeService(self.provider)
        self._snapshot_svc = GCESnapshotService(self.provider)
        self._bucket_svc = GCSBucketService(self.provider)

    @property
    def volumes(self):
        return self._volume_svc

    @property
    def snapshots(self):
        return self._snapshot_svc

    @property
    def buckets(self):
        return self._bucket_svc


class GCEVolumeService(BaseVolumeService):

    def __init__(self, provider):
        super(GCEVolumeService, self).__init__(provider)

    def get(self, volume_id):
        """
        Returns a volume given its id.
        """
        vol = self.provider.get_resource('disks', volume_id)
        return GCEVolume(self.provider, vol) if vol else None

    def find(self, label, limit=None, marker=None):
        """
        Searches for a volume by a given list of attributes.
        """
        filtr = 'labels.cblabel eq ' + label
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        gce_vols = [GCEVolume(self.provider, vol)
                    for vol in response.get('items', [])]
        if len(gce_vols) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(gce_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gce_vols)

    def list(self, limit=None, marker=None):
        """
        List all volumes.

        limit: The maximum number of volumes to return. The returned
               ResultList's is_truncated property can be used to determine
               whether more records are available.
        """
        # For GCE API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .disks()
                        .list(project=self.provider.project_name,
                              zone=self.provider.default_zone,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        gce_vols = [GCEVolume(self.provider, vol)
                    for vol in response.get('items', [])]
        if len(gce_vols) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(gce_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gce_vols)

    def create(self, label, size, zone, snapshot=None, description=None):
        """
        Creates a new volume.

        Argument `name` must be 1-63 characters long, and comply with RFC1035.
        Specifically, the name must be 1-63 characters long and match the
        regular expression [a-z]([-a-z0-9]*[a-z0-9])? which means the first
        character must be a lowercase letter, and all following characters must
        be a dash, lowercase letter, or digit, except the last character, which
        cannot be a dash.
        """
        log.debug("Creating GCE Volume with parameters "
                  "[label: %s size: %s zone: %s snapshot: %s "
                  "description: %s]", label, size, zone, snapshot,
                  description)
        GCEVolume.assert_valid_resource_label(label)
        name = GCEVolume._generate_name_from_label(label, 'cb-vol')
        if not isinstance(zone, GCEPlacementZone):
            zone = GCEPlacementZone(
                self.provider,
                self.provider.get_resource('zones', zone, zone=zone))
        zone_name = zone.name
        snapshot_id = snapshot.id if isinstance(
            snapshot, GCESnapshot) and snapshot else snapshot
        disk_body = {
            'name': name,
            'sizeGb': size,
            'type': 'zones/{0}/diskTypes/{1}'.format(zone_name, 'pd-standard'),
            'sourceSnapshot': snapshot_id,
            'description': description,
        }
        operation = (self.provider
                         .gce_compute
                         .disks()
                         .insert(
                             project=self._provider.project_name,
                             zone=zone_name,
                             body=disk_body)
                         .execute())
        cb_vol = self.get(operation.get('targetLink'))
        cb_vol.label = label
        return cb_vol


class GCESnapshotService(BaseSnapshotService):

    def __init__(self, provider):
        super(GCESnapshotService, self).__init__(provider)

    def get(self, snapshot_id):
        """
        Returns a snapshot given its id.
        """
        snapshot = self.provider.get_resource('snapshots', snapshot_id)
        return GCESnapshot(self.provider, snapshot) if snapshot else None

    def find(self, label, limit=None, marker=None):
        """
        Searches for a snapshot by a given list of attributes.
        """
        filtr = 'labels.cblabel eq ' + label
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              filter=filtr,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        snapshots = [GCESnapshot(self.provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    def list(self, limit=None, marker=None):
        """
        List all snapshots.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        response = (self.provider
                        .gce_compute
                        .snapshots()
                        .list(project=self.provider.project_name,
                              maxResults=max_result,
                              pageToken=marker)
                        .execute())
        snapshots = [GCESnapshot(self.provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            cb.log.warning('Expected at most %d results; got %d',
                           max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    def create(self, label, volume, description=None):
        """
        Creates a new snapshot of a given volume.
        """
        GCESnapshot.assert_valid_resource_label(label)
        name = GCESnapshot._generate_name_from_label(label, 'cbsnap')
        volume_name = volume.name if isinstance(volume, GCEVolume) else volume
        snapshot_body = {
            "name": name,
            "description": description
        }
        operation = (self.provider
                         .gce_compute
                         .disks()
                         .createSnapshot(
                             project=self.provider.project_name,
                             zone=self.provider.default_zone,
                             disk=volume_name, body=snapshot_body)
                         .execute())
        if 'zone' not in operation:
            return None
        self.provider.wait_for_operation(operation,
                                         zone=self.provider.default_zone)
        cb_snap = self.get(name)
        cb_snap.label = label
        return cb_snap


class GCSBucketService(BaseBucketService):

    def __init__(self, provider):
        super(GCSBucketService, self).__init__(provider)

    def get(self, bucket_id):
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist or if the user does not have permission to access the
        bucket.
        """
        bucket = self.provider.get_resource('buckets', bucket_id)
        return GCSBucket(self.provider, bucket) if bucket else None

    def find(self, name, limit=None, marker=None):
        """
        Searches in bucket names for a substring.
        """
        buckets = [bucket for bucket in self if name in bucket.name]
        return ClientPagedResultList(self.provider, buckets, limit=limit,
                                     marker=marker)

    def list(self, limit=None, marker=None):
        """
        List all containers.
        """
        max_result = limit if limit is not None and limit < 500 else 500
        try:
            response = (self.provider
                            .gcs_storage
                            .buckets()
                            .list(project=self.provider.project_name,
                                  maxResults=max_result,
                                  pageToken=marker)
                            .execute())
            if 'error' in response:
                return ServerPagedResultList(False, None, False, data=[])
            buckets = []
            for bucket in response.get('items', []):
                buckets.append(GCSBucket(self.provider, bucket))
            if len(buckets) > max_result:
                cb.log.warning('Expected at most %d results; got %d',
                               max_result, len(buckets))
            return ServerPagedResultList('nextPageToken' in response,
                                         response.get('nextPageToken'),
                                         False, data=buckets)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return ServerPagedResultList(False, None, False, data=[])

    def create(self, name, location=None):
        """
        Create a new bucket and returns it. Returns None if creation fails.
        """
        GCSBucket.assert_valid_resource_name(name)
        body = {'name': name}
        if location:
            body['location'] = location
        try:
            response = (self.provider
                            .gcs_storage
                            .buckets()
                            .insert(project=self.provider.project_name,
                                    body=body)
                            .execute())
            if 'error' in response:
                return None
            # GCS has a rate limit of 1 operation per 2 seconds for bucket
            # creation/deletion: https://cloud.google.com/storage/quotas.
            # Throttle here to avoid future failures.
            time.sleep(2)
            return GCSBucket(self.provider, response)
        except googleapiclient.errors.HttpError as http_error:
            cb.log.warning('googleapiclient.errors.HttpError: %s', http_error)
            return None
