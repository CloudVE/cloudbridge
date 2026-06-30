from __future__ import annotations

import builtins
import io
import ipaddress
import json
import logging
import time
import uuid
from typing import Any
from typing import TYPE_CHECKING
from typing import cast

import googleapiclient

from cloudbridge.base import helpers as cb_helpers
from cloudbridge.base.middleware import dispatch
from cloudbridge.base.resources import BaseMultipartUpload
from cloudbridge.base.resources import BaseUploadPart
from cloudbridge.base.resources import ClientPagedResultList
from cloudbridge.base.resources import ServerPagedResultList
from cloudbridge.base.services import BaseBucketObjectService
from cloudbridge.base.services import BaseBucketService
from cloudbridge.base.services import BaseComputeService
from cloudbridge.base.services import BaseDnsRecordService
from cloudbridge.base.services import BaseDnsService
from cloudbridge.base.services import BaseDnsZoneService
from cloudbridge.base.services import BaseFloatingIPService
from cloudbridge.base.services import BaseGatewayService
from cloudbridge.base.services import BaseImageService
from cloudbridge.base.services import BaseInstanceService
from cloudbridge.base.services import BaseKeyPairService
from cloudbridge.base.services import BaseNetworkService
from cloudbridge.base.services import BaseNetworkingService
from cloudbridge.base.services import BaseRegionService
from cloudbridge.base.services import BaseRouterService
from cloudbridge.base.services import BaseSecurityService
from cloudbridge.base.services import BaseSnapshotService
from cloudbridge.base.services import BaseStorageService
from cloudbridge.base.services import BaseSubnetService
from cloudbridge.base.services import BaseVMFirewallRuleService
from cloudbridge.base.services import BaseVMFirewallService
from cloudbridge.base.services import BaseVMTypeService
from cloudbridge.base.services import BaseVolumeService
from cloudbridge.interfaces.exceptions import DuplicateResourceException
from cloudbridge.interfaces.exceptions import InvalidParamException
from cloudbridge.interfaces.exceptions import ProviderInternalException
from cloudbridge.interfaces.resources import Bucket
from cloudbridge.interfaces.resources import BucketObject
from cloudbridge.interfaces.resources import DnsZone
from cloudbridge.interfaces.resources import FloatingIP
from cloudbridge.interfaces.resources import Gateway
from cloudbridge.interfaces.resources import KeyPair
from cloudbridge.interfaces.resources import LaunchConfig
from cloudbridge.interfaces.resources import MachineImage
from cloudbridge.interfaces.resources import MultipartUpload
from cloudbridge.interfaces.resources import Network
from cloudbridge.interfaces.resources import Region
from cloudbridge.interfaces.resources import ResultList
from cloudbridge.interfaces.resources import Router
from cloudbridge.interfaces.resources import Snapshot
from cloudbridge.interfaces.resources import Subnet
from cloudbridge.interfaces.resources import TrafficDirection
from cloudbridge.interfaces.resources import UploadPart
from cloudbridge.interfaces.resources import VMFirewall
from cloudbridge.interfaces.resources import VMType
from cloudbridge.interfaces.resources import Volume
from cloudbridge.providers.gcp import helpers

from .resources import GCPBucket
from .resources import GCPBucketObject
from .resources import GCPDnsRecord
from .resources import GCPDnsZone
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

if TYPE_CHECKING:
    from cloudbridge.interfaces.provider import CloudProvider
    from cloudbridge.providers.gcp.provider import GCPCloudProvider

log = logging.getLogger(__name__)


class GCPSecurityService(BaseSecurityService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPSecurityService, self).__init__(provider)

        # Initialize provider services
        self._key_pairs = GCPKeyPairService(provider)
        self._vm_firewalls = GCPVMFirewallService(provider)
        self._vm_firewall_rule_svc = GCPVMFirewallRuleService(provider)

    @property
    def key_pairs(self) -> GCPKeyPairService:
        return self._key_pairs

    @property
    def vm_firewalls(self) -> GCPVMFirewallService:
        return self._vm_firewalls

    @property
    def _vm_firewall_rules(self) -> GCPVMFirewallRuleService:
        return self._vm_firewall_rule_svc


class GCPKeyPairService(BaseKeyPairService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPKeyPairService, self).__init__(provider)

    @dispatch(event="provider.security.key_pairs.get",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def get(self, key_pair_id: str) -> GCPKeyPair | None:
        """
        Returns a KeyPair given its ID.
        """
        for kp in self:
            if kp.id == key_pair_id:
                return cast(GCPKeyPair, kp)
        else:
            return None

    @dispatch(event="provider.security.key_pairs.list",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPKeyPair]:
        provider = cast("GCPCloudProvider", self.provider)
        key_pairs = []
        for item in helpers.find_matching_metadata_items(
                provider, GCPKeyPair.KP_TAG_REGEX):
            metadata_value = json.loads(item['value'])
            kp_info = GCPKeyPair.GCPKeyInfo(**metadata_value)
            key_pairs.append(GCPKeyPair(provider, kp_info))
        return ClientPagedResultList(self.provider, key_pairs,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.security.key_pairs.find",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[GCPKeyPair]:
        """
        Searches for a key pair by a given list of attributes.
        """
        obj_list = list(self)
        filters = ['id', 'name']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, ", ".join(filters)))

        return ClientPagedResultList(
            self.provider,
            cast("builtins.list[GCPKeyPair]", matches) if matches else [])

    @dispatch(event="provider.security.key_pairs.create",
              priority=BaseKeyPairService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               public_key_material: str | None = None) -> GCPKeyPair:
        GCPKeyPair.assert_valid_resource_name(name)
        provider = cast("GCPCloudProvider", self.provider)
        private_key = None
        if not public_key_material:
            public_key_material, private_key = cb_helpers.generate_key_pair()
        # TODO: Add support for other formats not assume ssh-rsa
        elif "ssh-rsa" not in public_key_material:
            public_key_material = "ssh-rsa {}".format(public_key_material)
        kp_info = GCPKeyPair.GCPKeyInfo(name, public_key_material)
        metadata_value = json.dumps(kp_info._asdict())
        try:
            helpers.add_metadata_item(provider,
                                      GCPKeyPair.KP_TAG_PREFIX + name,
                                      metadata_value)
            return GCPKeyPair(provider, kp_info, private_key)
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
    def delete(self, key_pair: GCPKeyPair | str) -> None:
        provider = cast("GCPCloudProvider", self.provider)
        key_pair = (key_pair if isinstance(key_pair, GCPKeyPair) else
                    self.get(key_pair))
        if key_pair:
            helpers.remove_metadata_item(
                provider,
                GCPKeyPair.KP_TAG_PREFIX + key_pair.name)


class GCPVMFirewallService(BaseVMFirewallService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPVMFirewallService, self).__init__(provider)
        self._delegate = GCPFirewallsDelegate(
            cast("GCPCloudProvider", provider))

    @dispatch(event="provider.security.vm_firewalls.get",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_firewall_id: str) -> GCPVMFirewall | None:
        tag, network_name = \
            self._delegate.get_tag_network_from_id(vm_firewall_id)
        if tag is None or network_name is None:
            return None
        network = self.provider.networking.networks.get(network_name)
        return GCPVMFirewall(self._delegate, tag, network)

    @dispatch(event="provider.security.vm_firewalls.list",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPVMFirewall]:
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
    def create(self, label: str, network: Network | str,
               description: str | None = None) -> GCPVMFirewall:
        GCPVMFirewall.assert_valid_resource_label(label)
        network_obj = (network if isinstance(network, GCPNetwork)
                       else self.provider.networking.networks.get(cast(str, network)))
        fw = GCPVMFirewall(self._delegate, label, network_obj, description)
        fw.label = label
        # This rule exists implicitly. Add it explicitly so that the firewall
        # is not empty and the rule is shown by list/get/find methods.
        # create_with_priority is a GCP-only helper not on the public
        # VMFirewallRuleService interface; reach it via the typed sub-service.
        # pylint:disable=protected-access
        rule_svc = cast(GCPVMFirewallRuleService,
                        self.provider.security._vm_firewall_rules)
        rule_svc.create_with_priority(
            fw, direction=TrafficDirection.OUTBOUND, protocol='tcp',
            priority=65534, cidr='0.0.0.0/0')
        return fw

    @dispatch(event="provider.security.vm_firewalls.delete",
              priority=BaseVMFirewallService.STANDARD_EVENT_PRIORITY)
    def delete(self, vm_firewall: VMFirewall | str) -> None:
        fw_id = (vm_firewall.id if isinstance(vm_firewall, VMFirewall)
                 else vm_firewall)
        self._delegate.delete_tag_network_with_id(fw_id)

    def find_by_network_and_tags(
            self, network_name: str,
            tags: builtins.list[str]) -> builtins.list[GCPVMFirewall]:
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

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPVMFirewallRuleService, self).__init__(provider)
        self._dummy_rule: GCPVMFirewallRule | None = None

    @dispatch(event="provider.security.vm_firewall_rules.list",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def list(self, firewall: VMFirewall, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPVMFirewallRule]:
        gcp_fw = cast(GCPVMFirewall, firewall)
        rules = []
        for fw in gcp_fw.delegate.iter_firewalls(
                gcp_fw.name, gcp_fw.network.name):
            rule = GCPVMFirewallRule(firewall, fw['id'])
            if rule.is_dummy_rule():
                self._dummy_rule = rule
            else:
                rules.append(rule)
        return ClientPagedResultList(self.provider, rules,
                                     limit=limit, marker=marker)

    @property
    def dummy_rule(self) -> GCPVMFirewallRule | None:
        if not self._dummy_rule:
            self.list()
        return self._dummy_rule

    @staticmethod
    def to_port_range(from_port: int | None,
                      to_port: int | None) -> str | int | None:
        if from_port is not None and to_port is not None:
            return '%d-%d' % (from_port, to_port)
        elif from_port is not None:
            return from_port
        else:
            return to_port

    def create_with_priority(
            self, firewall: VMFirewall, direction: TrafficDirection,
            protocol: str | None, priority: int, from_port: int | None = None,
            to_port: int | None = None,
            cidr: str | builtins.list[str] | None = None,
            src_dest_fw: VMFirewall | None = None) -> GCPVMFirewallRule:
        gcp_fw = cast(GCPVMFirewall, firewall)
        port = GCPVMFirewallRuleService.to_port_range(from_port, to_port)
        src_dest_tag = None
        src_dest_fw_id = None
        if src_dest_fw:
            src_dest_tag = src_dest_fw.name
            src_dest_fw_id = src_dest_fw.id
        if not gcp_fw.delegate.add_firewall(
                gcp_fw.name, direction, protocol, priority, port, cidr,
                src_dest_tag, gcp_fw.description,
                gcp_fw.network.name):
            raise ProviderInternalException(
                "Failed to create the VM firewall rule")
        rules = self.find(firewall, direction=direction, protocol=protocol,
                          from_port=from_port, to_port=to_port, cidr=cidr,
                          src_dest_fw_id=src_dest_fw_id)
        if len(rules) < 1:
            raise ProviderInternalException(
                "VM firewall rule not found after creation")
        return cast(GCPVMFirewallRule, rules[0])

    # declares a non-optional VMFirewallRule.
    @dispatch(event="provider.security.vm_firewall_rules.create",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def create(self, firewall: VMFirewall,
               direction: TrafficDirection,
               protocol: str | None = None, from_port: int | None = None,
               to_port: int | None = None,
               cidr: str | builtins.list[str] | None = None,
               src_dest_fw: VMFirewall | None = None
               ) -> GCPVMFirewallRule:
        return self.create_with_priority(firewall, direction, protocol,
                                         1000, from_port, to_port, cidr,
                                         src_dest_fw)

    # The interface declares delete(firewall, rule_id: str); this impl also
    # accepts a GCPVMFirewallRule instance.
    @dispatch(event="provider.security.vm_firewall_rules.delete",
              priority=BaseVMFirewallRuleService.STANDARD_EVENT_PRIORITY)
    def delete(self, firewall: VMFirewall,
               rule: GCPVMFirewallRule | str) -> None:
        rule = cast(GCPVMFirewallRule,
                    rule if isinstance(rule, GCPVMFirewallRule)
                    else self.get(firewall, rule))
        if rule.is_dummy_rule():
            return
        cast(GCPVMFirewall, firewall).delegate.delete_firewall_id(rule._rule)


class GCPVMTypeService(BaseVMTypeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPVMTypeService, self).__init__(provider)

    @property
    def instance_data(self) -> Any:
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_compute
            .machineTypes()
            .list(project=provider.project_name,
                  zone=provider.zone_name)
            .execute())
        return response['items']

    @dispatch(event="provider.compute.vm_types.get",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def get(self, vm_type_id: str) -> GCPVMType | None:
        provider = cast("GCPCloudProvider", self.provider)
        vm_type = provider.get_resource('machineTypes', vm_type_id)
        return GCPVMType(provider, vm_type) if vm_type else None

    @dispatch(event="provider.compute.vm_types.find",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[GCPVMType]:
        provider = cast("GCPCloudProvider", self.provider)
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
                matched_inst_types.append(GCPVMType(provider, inst_type))
        return ClientPagedResultList(self.provider, matched_inst_types)

    @dispatch(event="provider.compute.vm_types.list",
              priority=BaseVMTypeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPVMType]:
        provider = cast("GCPCloudProvider", self.provider)
        inst_types = [GCPVMType(provider, inst_type)
                      for inst_type in self.instance_data]
        return ClientPagedResultList(self.provider, inst_types,
                                     limit=limit, marker=marker)


class GCPRegionService(BaseRegionService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPRegionService, self).__init__(provider)

    @dispatch(event="provider.compute.regions.get",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def get(self, region_id: str) -> GCPRegion | None:
        provider = cast("GCPCloudProvider", self.provider)
        region = provider.get_resource(
            'regions', region_id, region=region_id)
        return GCPRegion(provider, region) if region else None

    @dispatch(event="provider.compute.regions.list",
              priority=BaseRegionService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPRegion]:
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        regions_response = (
            provider
            .gcp_compute
            .regions()
            .list(project=provider.project_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        regions = [GCPRegion(provider, region)
                   for region in regions_response['items']]
        if len(regions) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(regions))
        return ServerPagedResultList('nextPageToken' in regions_response,
                                     regions_response.get('nextPageToken'),
                                     False, data=regions)

    @property
    def current(self) -> GCPRegion | None:
        return self.get(self.provider.region_name)


class GCPImageService(BaseImageService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPImageService, self).__init__(provider)
        self._public_images: builtins.list[GCPMachineImage] | None = None

    _PUBLIC_IMAGE_PROJECTS = ['centos-cloud', 'coreos-cloud', 'debian-cloud',
                              'opensuse-cloud', 'ubuntu-os-cloud', 'cos-cloud']

    def _retrieve_public_images(self) -> None:
        if self._public_images is not None:
            return
        self._public_images = []
        provider = cast("GCPCloudProvider", self.provider)
        for project in GCPImageService._PUBLIC_IMAGE_PROJECTS:
            for image in helpers.iter_all(
                    provider.gcp_compute.images(), project=project):
                self._public_images.append(
                    GCPMachineImage(provider, image))

    def get(self, image_id: str) -> GCPMachineImage | None:
        """
        Returns an Image given its id
        """
        provider = cast("GCPCloudProvider", self.provider)
        image = provider.get_resource(
            'images', image_id)
        if image:
            return GCPMachineImage(provider, image)
        self._retrieve_public_images()
        for public_image in self._public_images or []:
            if public_image.id == image_id or public_image.name == image_id:
                return public_image
        return None

    # The interface declares find(self, **kwargs); this impl also accepts
    # leading limit/marker pagination params.
    def find(self,  # type: ignore[override]
             limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPMachineImage]:
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
        return ClientPagedResultList(
            self.provider, cast("builtins.list[GCPMachineImage]", images),
            limit=limit, marker=marker)

    # The interface declares list(self, filter_by_owner, limit, marker); this
    # impl omits filter_by_owner.
    def list(self, limit: int | None = None,  # type: ignore[override]
             marker: str | None = None) -> ResultList[GCPMachineImage]:
        """
        List all images.
        """
        self._retrieve_public_images()
        provider = cast("GCPCloudProvider", self.provider)
        images = []
        if (provider.project_name not in
                GCPImageService._PUBLIC_IMAGE_PROJECTS):
            for image in helpers.iter_all(
                    provider.gcp_compute.images(),
                    project=provider.project_name):
                images.append(GCPMachineImage(provider, image))
        images.extend(self._public_images or [])
        return ClientPagedResultList(self.provider, images,
                                     limit=limit, marker=marker)


class GCPInstanceService(BaseInstanceService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPInstanceService, self).__init__(provider)

    @dispatch(event="provider.compute.instances.create",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, image: MachineImage | str,
               vm_type: VMType | str, subnet: Subnet | str,
               key_pair: KeyPair | str | None = None,
               vm_firewalls: builtins.list[VMFirewall] | builtins.list[str] | None = None,
               user_data: str | None = None,
               launch_config: LaunchConfig | None = None,
               **kwargs: Any) -> GCPInstance:
        """
        Creates a new virtual machine instance.
        """
        GCPInstance.assert_valid_resource_name(label)
        zone_name = self.provider.zone_name
        vm_type_obj: VMType | None = (
            vm_type if isinstance(vm_type, GCPVMType)
            else self.provider.compute.vm_types.get(cast(str, vm_type)))

        network_interface: dict[str, Any] = {
            'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                               'name': 'External NAT'}]}
        if subnet:
            network_interface['subnetwork'] = cast(Subnet, subnet).id
        else:
            network_interface['network'] = 'global/networks/default'

        num_roots = 0
        disks: builtins.list[dict[str, Any]] = []
        boot_disk: dict[str, Any] | None = None
        source_value: Any
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
                image_obj: MachineImage | None = (
                    image if isinstance(image, GCPMachineImage)
                    else self.provider.compute.images.get(cast(str, image)))
                # Explicitly set diskName; otherwise, instance name will be
                # used by default which may conflict with existing disks.
                boot_disk = {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': cast(MachineImage, image_obj).id,
                        'diskName': 'image-disk-{0}'.format(uuid.uuid4())}}

        if not boot_disk:
            raise ProviderInternalException(
                'No boot disk is given for instance {0}.'.format(label))
        # The boot disk must be the first disk attached to the instance.
        disks.insert(0, boot_disk)

        config: dict[str, Any] = {
            'name': GCPInstance._generate_name_from_label(label, 'cb-inst'),
            'machineType': cast(GCPVMType, vm_type_obj).resource_url,
            'disks': disks,
            'networkInterfaces': [network_interface]
        }

        service_accounts = kwargs.pop('service_accounts', None)
        if service_accounts:
            config['serviceAccounts'] = service_accounts

        if vm_firewalls and isinstance(vm_firewalls, list):
            vm_firewall_names: builtins.list[str] = []
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
            key_pair_obj: KeyPair | None = (
                key_pair if isinstance(key_pair, GCPKeyPair)
                else self._provider.security.key_pairs.get(cast(str, key_pair)))
            if key_pair_obj:
                kp = cast(GCPKeyPair, key_pair_obj)._key_pair
                kp_entry = {
                    "key": "ssh-keys",
                    # Format is not removed from public key portion
                    "value": "{}:{} {}".format(
                        cast("GCPCloudProvider",
                             self.provider).vm_default_user_name,
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

        provider = cast("GCPCloudProvider", self.provider)
        operation = (
            provider
            .gcp_compute.instances()
            .insert(project=provider.project_name,
                    zone=zone_name,
                    body=config)
            .execute())
        instance_id = operation.get('targetLink')
        provider.wait_for_operation(operation, zone=zone_name)
        cb_inst = self.get(instance_id)
        return cb_inst

    @dispatch(event="provider.compute.instances.get",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def get(self, instance_id: str) -> GCPInstance | None:
        """
        Returns an instance given its name. Returns None
        if the object does not exist.

        A GCP instance is uniquely identified by its selfLink, which is used
        as its id.
        """
        provider = cast("GCPCloudProvider", self.provider)
        instance = provider.get_resource('instances', instance_id)
        return (GCPInstance(provider, instance)
                if instance else None)

    @dispatch(event="provider.compute.instances.find",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def find(self, limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPInstance]:
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
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPInstance]:
        """
        List all instances.
        """
        provider = cast("GCPCloudProvider", self.provider)
        # For GCP API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .instances()
            .list(project=provider.project_name,
                  zone=provider.zone_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        instances = [
            GCPInstance(provider, inst)
            for inst in response.get('items', [])]
        if len(instances) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(instances))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=instances)

    @dispatch(event="provider.compute.instances.delete",
              priority=BaseInstanceService.STANDARD_EVENT_PRIORITY)
    def delete(self, instance: GCPInstance | str) -> None:
        provider = cast("GCPCloudProvider", self.provider)
        instance = (instance if isinstance(instance, GCPInstance) else
                    self.get(instance))
        if instance:
            (provider
             .gcp_compute
             .instances()
             .delete(project=cast("GCPCloudProvider",
                                  self.provider).project_name,
                     zone=instance.zone_name,
                     instance=instance.name)
             .execute())

    def create_launch_config(self) -> GCPLaunchConfig:
        provider = cast("GCPCloudProvider", self.provider)
        return GCPLaunchConfig(provider)


class GCPComputeService(BaseComputeService):
    # TODO: implement GCPComputeService
    def __init__(self, provider: CloudProvider) -> None:
        super(GCPComputeService, self).__init__(provider)
        self._instance_svc = GCPInstanceService(self.provider)
        self._vm_type_svc = GCPVMTypeService(self.provider)
        self._region_svc = GCPRegionService(self.provider)
        self._images_svc = GCPImageService(self.provider)

    @property
    def images(self) -> GCPImageService:
        return self._images_svc

    @property
    def vm_types(self) -> GCPVMTypeService:
        return self._vm_type_svc

    @property
    def instances(self) -> GCPInstanceService:
        return self._instance_svc

    @property
    def regions(self) -> GCPRegionService:
        return self._region_svc


class GCPNetworkingService(BaseNetworkingService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPNetworkingService, self).__init__(provider)
        self._network_service = GCPNetworkService(self.provider)
        self._subnet_service = GCPSubnetService(self.provider)
        self._router_service = GCPRouterService(self.provider)
        self._gateway_service = GCPGatewayService(self.provider)
        self._floating_ip_service = GCPFloatingIPService(self.provider)

    @property
    def networks(self) -> GCPNetworkService:
        return self._network_service

    @property
    def subnets(self) -> GCPSubnetService:
        return self._subnet_service

    @property
    def routers(self) -> GCPRouterService:
        return self._router_service

    @property
    def _gateways(self) -> GCPGatewayService:
        return self._gateway_service

    @property
    def _floating_ips(self) -> GCPFloatingIPService:
        return self._floating_ip_service


class GCPNetworkService(BaseNetworkService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPNetworkService, self).__init__(provider)

    @dispatch(event="provider.networking.networks.get",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def get(self, network_id: str) -> GCPNetwork | None:
        provider = cast("GCPCloudProvider", self.provider)
        network = provider.get_resource(
            'networks', network_id)
        return GCPNetwork(provider, network) if network else None

    @dispatch(event="provider.networking.networks.find",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def find(self, limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPNetwork]:
        """
        GCP networks are global. There is at most one network with a given
        name.
        """
        obj_list = list(self)
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(
            self._provider, cast("builtins.list[GCPNetwork]", matches),
            limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.list",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None, marker: str | None = None,
             filter: str | None = None) -> ResultList[GCPNetwork]:
        # TODO: Decide whether we keep filter in 'list'
        provider = cast("GCPCloudProvider", self.provider)
        networks = []
        response = (
            provider
            .gcp_compute
            .networks()
            .list(project=provider.project_name,
                  filter=filter)
            .execute())
        for network in response.get('items', []):
            networks.append(GCPNetwork(provider, network))
        return ClientPagedResultList(self.provider, networks,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.networks.create",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, cidr_block: str) -> GCPNetwork:
        """
        Creates an auto mode VPC network with default subnets. It is possible
        to add additional subnets later.
        """
        GCPNetwork.assert_valid_resource_label(label)
        name = GCPNetwork._generate_name_from_label(label, 'cbnet')
        body: dict[str, Any] = {'name': name}
        # This results in a custom mode network
        body['autoCreateSubnetworks'] = False
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_compute
            .networks()
            .insert(project=provider.project_name,
                    body=body)
            .execute())
        provider.wait_for_operation(response)
        # The network is expected to exist immediately after creation.
        cb_net = cast(GCPNetwork, self.get(name))
        cb_net.label = label
        return cb_net

    def get_or_create_default(self) -> GCPNetwork:
        default_nets = self.provider.networking.networks.find(
            label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
        if default_nets:
            return cast(GCPNetwork, default_nets[0])
        else:
            log.info("Creating a CloudBridge-default network labeled %s",
                     GCPNetwork.CB_DEFAULT_NETWORK_LABEL)
            return self.create(
                label=GCPNetwork.CB_DEFAULT_NETWORK_LABEL,
                cidr_block=GCPNetwork.CB_DEFAULT_IPV4RANGE)

    @dispatch(event="provider.networking.networks.delete",
              priority=BaseNetworkService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str) -> None:
        # Accepts network object
        if not isinstance(network, str):
            name = network.name
        # Accepts both name and ID
        elif 'googleapis' in network:
            name = network.split('/')[-1]
        else:
            name = network
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_compute
            .networks()
            .delete(project=provider.project_name,
                    network=name)
            .execute())
        provider.wait_for_operation(response)
        # Remove label
        tag_name = "_".join(["network", name, "label"])
        if not helpers.remove_metadata_item(
                provider, tag_name):
            log.warning('No label was found associated with this network '
                        '"{}" when deleted.'.format(network))


class GCPRouterService(BaseRouterService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPRouterService, self).__init__(provider)

    @dispatch(event="provider.networking.routers.get",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def get(self, router_id: str) -> GCPRouter | None:
        provider = cast("GCPCloudProvider", self.provider)
        router = provider.get_resource(
            'routers', router_id, region=self.provider.region_name)
        return GCPRouter(provider, router) if router else None

    @dispatch(event="provider.networking.routers.find",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def find(self, limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPRouter]:
        obj_list = list(self)
        filters = ['name', 'label']
        matches = cb_helpers.generic_find(filters, kwargs, obj_list)
        return ClientPagedResultList(
            self._provider, cast("builtins.list[GCPRouter]", matches),
            limit=limit, marker=marker)

    @dispatch(event="provider.networking.routers.list",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPRouter]:
        provider = cast("GCPCloudProvider", self.provider)
        region = self.provider.region_name
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .routers()
            .list(project=provider.project_name,
                  region=region,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        routers = []
        for router in response.get('items', []):
            routers.append(GCPRouter(provider, router))
        if len(routers) > max_result:
            log.warning('Expected at most %d results; go %d',
                        max_result, len(routers))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=routers)

    @dispatch(event="provider.networking.routers.create",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str) -> GCPRouter:
        log.debug("Creating GCP Router Service with params "
                  "[label: %s network: %s]", label, network)
        GCPRouter.assert_valid_resource_label(label)
        name = GCPRouter._generate_name_from_label(label, 'cb-router')

        network_obj = (network if isinstance(network, GCPNetwork)
                       else self.provider.networking.networks.get(cast(str, network)))
        network_url = cast(GCPNetwork, network_obj).resource_url
        provider = cast("GCPCloudProvider", self.provider)
        region_name = self.provider.region_name
        response = (
            provider
            .gcp_compute
            .routers()
            .insert(project=provider.project_name,
                    region=region_name,
                    body={'name': name,
                          'network': network_url})
            .execute())
        provider.wait_for_operation(response, region=region_name)
        # The router is expected to exist immediately after creation.
        cb_router = cast(GCPRouter, self.get(name))
        cb_router.label = label
        return cb_router

    @dispatch(event="provider.networking.routers.delete",
              priority=BaseRouterService.STANDARD_EVENT_PRIORITY)
    def delete(self, router: Router | str) -> None:
        r = router if isinstance(router, GCPRouter) else self.get(router)
        if r:
            provider = cast("GCPCloudProvider", self.provider)
            (provider
             .gcp_compute
             .routers()
             .delete(project=provider.project_name,
                     region=r.region_name,
                     router=r.name)
             .execute())
            # Remove label
            tag_name = "_".join(["router", r.name, "label"])
            if not helpers.remove_metadata_item(
                    provider, tag_name):
                log.warning('No label was found associated with this router '
                            '"{}" when deleted.'.format(r.name))

    def _get_in_region(self, router_id: str,
                       region: Region | str | None = None) -> GCPRouter | None:
        region_name = self.provider.region_name
        if region:
            region_obj = (region if isinstance(region, GCPRegion)
                          else self.provider.compute.regions.get(cast(str, region)))
            region_name = cast(GCPRegion, region_obj).name
        provider = cast("GCPCloudProvider", self.provider)
        router = provider.get_resource(
            'routers', router_id, region=region_name)
        return GCPRouter(provider, router) if router else None


class GCPSubnetService(BaseSubnetService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPSubnetService, self).__init__(provider)

    @dispatch(event="provider.networking.subnets.get",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def get(self, subnet_id: str) -> GCPSubnet | None:
        provider = cast("GCPCloudProvider", self.provider)
        subnet = provider.get_resource('subnetworks', subnet_id)
        return GCPSubnet(provider, subnet) if subnet else None

    @dispatch(event="provider.networking.subnets.list",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str | None = None,
             limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPSubnet]:
        filter = None
        if network is not None:
            network_obj = (network if isinstance(network, GCPNetwork)
                           else self.provider.networking.networks.get(cast(str, network)))
            filter = ('network eq %s'
                      % cast(GCPNetwork, network_obj).resource_url)
        provider = cast("GCPCloudProvider", self.provider)
        region_name = self.provider.region_name
        subnets = []
        response = (
            provider
            .gcp_compute
            .subnetworks()
            .list(project=provider.project_name,
                  region=region_name,
                  filter=filter)
            .execute())
        for subnet in response.get('items', []):
            subnets.append(GCPSubnet(provider, subnet))
        return ClientPagedResultList(self.provider, subnets,
                                     limit=limit, marker=marker)

    @dispatch(event="provider.networking.subnets.create",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, network: Network | str,
               cidr_block: str) -> GCPSubnet:
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
                'network': cast(GCPNetwork, network).resource_url,
                'region': region_name
                }
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_compute
            .subnetworks()
            .insert(project=provider.project_name,
                    region=region_name,
                    body=body)
            .execute())
        provider.wait_for_operation(response, region=region_name)
        # The subnet is expected to exist immediately after creation.
        cb_subnet = cast(GCPSubnet, self.get(name))
        cb_subnet.label = label
        return cb_subnet

    @dispatch(event="provider.networking.subnets.delete",
              priority=BaseSubnetService.STANDARD_EVENT_PRIORITY)
    def delete(self, subnet: Subnet | str) -> None:
        sn = subnet if isinstance(subnet, GCPSubnet) else self.get(subnet)
        if not sn:
            return
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_compute
            .subnetworks()
            .delete(project=provider.project_name,
                    region=sn.region_name,
                    subnetwork=sn.name)
            .execute())
        provider.wait_for_operation(response, region=sn.region_name)
        # Remove label
        tag_name = "_".join(["subnet", sn.name, "label"])
        if not helpers.remove_metadata_item(
                provider, tag_name):
            log.warning('No label was found associated with this subnet '
                        '"{}" when deleted.'.format(sn.name))

    def get_or_create_default(self) -> GCPSubnet:
        """
        Return an existing or create a new subnet in the provider default zone.

        In GCP, subnets are a regional resource so a single subnet can services
        an entire region.
        """
        region_name = self.provider.region_name
        # Check if a default subnet already exists for the given region/zone
        for sn in self.find(label=GCPSubnet.CB_DEFAULT_SUBNET_LABEL):
            if sn.region_name == region_name:
                return cast(GCPSubnet, sn)
        # No default subnet in the current zone. Look for a default network,
        # then create a subnet whose address space does not overlap with any
        # other existing subnets. If there are existing subnets, this process
        # largely assumes the subnet address spaces are contiguous when it
        # does the calculations (e.g., 10.0.0.0/24, 10.0.1.0/24).
        cidr_block = GCPSubnet.CB_DEFAULT_SUBNET_IPV4RANGE
        # get_or_create_default lives on the GCP/base service, not the public
        # NetworkService/RouterService interface.
        nets = cast(GCPNetworkService, self.provider.networking.networks)
        net = nets.get_or_create_default()
        subnet_list = list(net.subnets)
        if subnet_list:
            max_sn = subnet_list[0]
            # Find the maximum address subnet address space within the network
            for esn in net.subnets:
                if (cast(Any, ipaddress.ip_network(esn.cidr_block)) >
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
        routers = cast(GCPRouterService, self.provider.networking.routers)
        router = routers.get_or_create_default(net)
        router.attach_subnet(sn)
        gateway = net.gateways.get_or_create()
        router.attach_gateway(gateway)
        return cast(GCPSubnet, sn)


class GCPStorageService(BaseStorageService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPStorageService, self).__init__(provider)

        # Initialize provider services
        self._volume_svc = GCPVolumeService(self.provider)
        self._snapshot_svc = GCPSnapshotService(self.provider)
        self._bucket_svc = GCPBucketService(self.provider)
        self._bucket_obj_svc = GCPBucketObjectService(self.provider)

    @property
    def volumes(self) -> GCPVolumeService:
        return self._volume_svc

    @property
    def snapshots(self) -> GCPSnapshotService:
        return self._snapshot_svc

    @property
    def buckets(self) -> GCPBucketService:
        return self._bucket_svc

    @property
    def _bucket_objects(self) -> GCPBucketObjectService:
        return self._bucket_obj_svc


class GCPVolumeService(BaseVolumeService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPVolumeService, self).__init__(provider)

    @dispatch(event="provider.storage.volumes.get",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def get(self, volume_id: str) -> GCPVolume | None:
        provider = cast("GCPCloudProvider", self.provider)
        vol = provider.get_resource(
            'disks', volume_id)
        return GCPVolume(provider, vol) if vol else None

    @dispatch(event="provider.storage.volumes.find",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def find(self, limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPVolume]:
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
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .disks()
            .list(project=provider.project_name,
                  zone=provider.zone_name,
                  filter=filtr,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        gcp_vols = [GCPVolume(provider, vol)
                    for vol in response.get('items', [])]
        if len(gcp_vols) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(gcp_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gcp_vols)

    @dispatch(event="provider.storage.volumes.list",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPVolume]:
        """
        List all volumes.

        limit: The maximum number of volumes to return. The returned
               ResultList's is_truncated property can be used to determine
               whether more records are available.
        """
        provider = cast("GCPCloudProvider", self.provider)
        # For GCP API, Acceptable values are 0 to 500, inclusive.
        # (Default: 500).
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .disks()
            .list(project=provider.project_name,
                  zone=provider.zone_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        gcp_vols = [GCPVolume(provider, vol)
                    for vol in response.get('items', [])]
        if len(gcp_vols) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(gcp_vols))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=gcp_vols)

    @dispatch(event="provider.storage.volumes.create",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, size: int,
               snapshot: Snapshot | str | None = None,
               description: str | None = None) -> GCPVolume:
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
        provider = cast("GCPCloudProvider", self.provider)
        operation = (
            provider
            .gcp_compute
            .disks()
            .insert(
                project=provider.project_name,
                zone=zone_name,
                body=disk_body)
            .execute())
        cb_vol = self.get(operation.get('targetLink'))
        return cb_vol

    @dispatch(event="provider.storage.volumes.delete",
              priority=BaseVolumeService.STANDARD_EVENT_PRIORITY)
    def delete(self, volume: Volume | str) -> None:
        volume = volume if isinstance(volume, GCPVolume) else self.get(volume)
        if volume:
            provider = cast("GCPCloudProvider", self.provider)
            (provider.gcp_compute
                     .disks()
                     .delete(project=provider.project_name,
                             zone=volume.zone_name,
                             disk=volume.name)
                     .execute())


class GCPSnapshotService(BaseSnapshotService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPSnapshotService, self).__init__(provider)

    @dispatch(event="provider.storage.snapshots.get",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def get(self, snapshot_id: str) -> GCPSnapshot | None:
        provider = cast("GCPCloudProvider", self.provider)
        snapshot = provider.get_resource(
            'snapshots', snapshot_id)
        return GCPSnapshot(provider, snapshot) if snapshot else None

    @dispatch(event="provider.storage.snapshots.find",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def find(self, limit: int | None = None, marker: str | None = None,
             **kwargs: Any) -> ResultList[GCPSnapshot]:
        label = kwargs.pop('label', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'label'))

        filtr = 'labels.cblabel eq ' + label
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .snapshots()
            .list(project=provider.project_name,
                  filter=filtr,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        snapshots = [GCPSnapshot(provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    @dispatch(event="provider.storage.snapshots.list",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPSnapshot]:
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .snapshots()
            .list(project=provider.project_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        snapshots = [GCPSnapshot(provider, snapshot)
                     for snapshot in response.get('items', [])]
        if len(snapshots) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(snapshots))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=snapshots)

    @dispatch(event="provider.storage.snapshots.create",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def create(self, label: str, volume: Volume | str,
               description: str | None = None) -> GCPSnapshot:
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
        provider = cast("GCPCloudProvider", self.provider)
        operation = (
            provider
            .gcp_compute
            .disks()
            .createSnapshot(
                project=provider.project_name,
                zone=provider.zone_name,
                disk=volume_name, body=snapshot_body)
            .execute())
        if 'zone' not in operation:
            raise ProviderInternalException(
                "Snapshot creation did not return a zoned operation")
        provider.wait_for_operation(operation, zone=provider.zone_name)
        cb_snap = self.get(name)
        return cb_snap

    @dispatch(event="provider.storage.snapshots.delete",
              priority=BaseSnapshotService.STANDARD_EVENT_PRIORITY)
    def delete(self, snapshot: Snapshot | str) -> None:
        snapshot = (snapshot if isinstance(snapshot, GCPSnapshot)
                    else self.get(snapshot))
        if snapshot:
            provider = cast("GCPCloudProvider", self.provider)
            (provider
             .gcp_compute
             .snapshots()
             .delete(project=provider.project_name,
                     snapshot=snapshot.name)
             .execute())


class GCPBucketService(BaseBucketService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPBucketService, self).__init__(provider)

    @dispatch(event="provider.storage.buckets.get",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def get(self, bucket_id: str) -> GCPBucket | None:
        """
        Returns a bucket given its ID. Returns ``None`` if the bucket
        does not exist or if the user does not have permission to access the
        bucket.
        """
        provider = cast("GCPCloudProvider", self.provider)
        bucket = provider.get_resource(
            'buckets', bucket_id)
        return GCPBucket(provider, bucket) if bucket else None

    @dispatch(event="provider.storage.buckets.find",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[GCPBucket]:
        name = kwargs.pop('name', None)

        # All kwargs should have been popped at this time.
        if len(kwargs) > 0:
            raise InvalidParamException(
                "Unrecognised parameters for search: %s. Supported "
                "attributes: %s" % (kwargs, 'name'))

        buckets = [bucket for bucket in self if name in bucket.name]
        return ClientPagedResultList(
            self.provider, cast("builtins.list[GCPBucket]", buckets))

    @dispatch(event="provider.storage.buckets.list",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPBucket]:
        """
        List all containers.
        """
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_storage
            .buckets()
            .list(project=provider.project_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        buckets = []
        for bucket in response.get('items', []):
            buckets.append(GCPBucket(provider, bucket))
        if len(buckets) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(buckets))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=buckets)

    @dispatch(event="provider.storage.buckets.create",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str,
               location: Region | str | None = None) -> GCPBucket:
        GCPBucket.assert_valid_resource_name(name)
        body: dict[str, Any] = {'name': name}
        if location:
            body['location'] = location
        try:
            provider = cast("GCPCloudProvider", self.provider)
            response = (
                provider
                .gcp_storage
                .buckets()
                .insert(project=provider.project_name,
                        body=body)
                .execute())
            # GCP has a rate limit of 1 operation per 2 seconds for bucket
            # creation/deletion: https://cloud.google.com/storage/quotas.
            # Throttle here to avoid future failures.
            time.sleep(2)
            return GCPBucket(provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # 409 = conflict
            if http_error.resp.status in [409]:
                raise DuplicateResourceException(
                    'Bucket already exists with name {0}'.format(name))
            else:
                raise

    @dispatch(event="provider.storage.buckets.delete",
              priority=BaseBucketService.STANDARD_EVENT_PRIORITY)
    def delete(self, bucket: Bucket | str) -> None:
        """
        Delete this bucket.
        """
        provider = cast("GCPCloudProvider", self.provider)
        b = bucket if isinstance(bucket, GCPBucket) else self.get(bucket)
        if b:
            (provider
             .gcp_storage
             .buckets()
             .delete(bucket=b.name)
             .execute())
            # GCP has a rate limit of 1 operation per 2 seconds for bucket
            # creation/deletion: https://cloud.google.com/storage/quotas.
            # Throttle here to avoid future failures.
            time.sleep(2)


class GCPBucketObjectService(BaseBucketObjectService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPBucketObjectService, self).__init__(provider)

    def get(self, bucket: Bucket | str,
            name: str) -> GCPBucketObject | None:
        """
        Retrieve a given object from this bucket.
        """
        provider = cast("GCPCloudProvider", self.provider)
        obj = provider.get_resource(
            'objects', name, bucket=cast(GCPBucket, bucket).name)
        return GCPBucketObject(provider, cast(Bucket, bucket), obj) if obj else None

    # The interface declares list(bucket, prefix, limit, marker); this impl
    # orders the optional parameters as (limit, marker, prefix).
    def list(self, bucket: Bucket | str,  # type: ignore[override]
             limit: int | None = None, marker: str | None = None,
             prefix: str | None = None) -> ResultList[GCPBucketObject]:
        """
        List all objects within this bucket.
        """
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_storage
            .objects()
            .list(bucket=cast(GCPBucket, bucket).name,
                  prefix=prefix if prefix else '',
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        objects = []
        for obj in response.get('items', []):
            objects.append(GCPBucketObject(provider, cast(Bucket, bucket), obj))
        if len(objects) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(objects))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=objects)

    # ResultList is invariant, so the return is typed with the interface
    # element type (BucketObject) rather than GCPBucketObject.
    def find(self, bucket: Bucket | str,
             **kwargs: Any) -> ResultList[BucketObject]:
        filters = ['name']
        matches = cb_helpers.generic_find(
            filters, kwargs, list(cast(GCPBucket, bucket).objects))
        return ClientPagedResultList(
            self._provider, list(matches), limit=None, marker=None)

    def _create_object_with_media_body(self, bucket: Bucket | str,
                                       name: str, media_body: Any) -> Any:
        provider = cast("GCPCloudProvider", self.provider)
        response = (
            provider
            .gcp_storage
            .objects()
            .insert(bucket=cast(GCPBucket, bucket).name,
                    body={'name': name},
                    media_body=media_body)
            .execute())
        return response

    def create(self, bucket: Bucket | str,
               name: str) -> GCPBucketObject:
        provider = cast("GCPCloudProvider", self.provider)
        response = self._create_object_with_media_body(
            bucket,
            name,
            googleapiclient.http.MediaIoBaseUpload(
                io.BytesIO(b''), mimetype='plain/text'))
        if not response:
            raise ProviderInternalException(
                "Failed to create bucket object {0}".format(name))
        return GCPBucketObject(provider, cast(Bucket, bucket), response)

    # GCS has no independent "upload part" API, so multipart is emulated by
    # uploading each part as a temporary object and assembling them with the
    # compose API. ``compose`` accepts at most this many source objects per
    # call, so larger uploads are composed in chained batches.
    _MAX_COMPOSE_SOURCES = 32

    @staticmethod
    def _temp_prefix(upload: MultipartUpload) -> str:
        return ".cb-mpu/{0}/{1}/".format(upload.object_name, upload.id)

    @classmethod
    def _temp_part_name(cls, upload: MultipartUpload,
                        part_number: int) -> str:
        return "{0}part-{1:05d}".format(cls._temp_prefix(upload), part_number)

    @dispatch(event="provider.storage._bucket_objects.create_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def create_multipart_upload(self, bucket: Bucket | str,
                                object_name: str) -> MultipartUpload:
        # No server-side initiation; the upload id namespaces this upload's
        # temporary part objects.
        return BaseMultipartUpload(self.provider, cast(Bucket, bucket),
                                   object_name, uuid.uuid4().hex)

    @dispatch(event="provider.storage._bucket_objects.upload_part",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def upload_part(self, bucket: Bucket | str, upload: MultipartUpload,
                    part_number: int, data: Any) -> UploadPart:
        if isinstance(data, str):
            data = data.encode()
        if isinstance(data, (bytes, bytearray)):
            data = io.BytesIO(data)
        media_body = googleapiclient.http.MediaIoBaseUpload(
            data, mimetype='application/octet-stream')
        temp_name = self._temp_part_name(upload, part_number)
        self._create_object_with_media_body(bucket, temp_name, media_body)
        return BaseUploadPart(part_number, temp_name)

    @dispatch(event="provider.storage._bucket_objects."
                    "complete_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def complete_multipart_upload(self, bucket: Bucket | str,
                                  upload: MultipartUpload,
                                  parts: builtins.list[UploadPart]
                                  ) -> GCPBucketObject | None:
        ordered = sorted(parts, key=lambda p: p.part_number)
        sources = cast("builtins.list[str]", [p.etag for p in ordered])
        intermediates = self._compose(bucket, upload, upload.object_name,
                                      sources)
        # The temporary part objects and any compose intermediates are real,
        # billable objects, so remove them once assembled.
        self._delete_objects(bucket, sources + intermediates,
                             ignore_missing=True)
        return self.get(bucket, upload.object_name)

    @dispatch(event="provider.storage._bucket_objects.abort_multipart_upload",
              priority=BaseBucketObjectService.STANDARD_EVENT_PRIORITY)
    def abort_multipart_upload(self, bucket: Bucket | str,
                               upload: MultipartUpload) -> None:
        self._delete_objects(bucket, self._list_temp_objects(bucket, upload),
                             ignore_missing=True)

    def _compose(self, bucket: Bucket | str, upload: MultipartUpload,
                 destination: str, sources: builtins.list[str]) -> builtins.list[str]:
        """
        Compose ``sources`` into ``destination``, chaining through
        intermediate objects when there are more than ``_MAX_COMPOSE_SOURCES``.
        Returns the list of intermediate object names created (to be cleaned
        up by the caller).
        """
        intermediates = []
        level = sources
        batch = 0
        while len(level) > self._MAX_COMPOSE_SOURCES:
            next_level = []
            for i in range(0, len(level), self._MAX_COMPOSE_SOURCES):
                group = level[i:i + self._MAX_COMPOSE_SOURCES]
                name = "{0}compose-{1:05d}".format(
                    self._temp_prefix(upload), batch)
                self._compose_once(bucket, name, group)
                intermediates.append(name)
                next_level.append(name)
                batch += 1
            level = next_level
        self._compose_once(bucket, destination, level)
        return intermediates

    def _compose_once(self, bucket: Bucket | str, destination: str,
                      sources: builtins.list[str]) -> None:
        provider = cast("GCPCloudProvider", self.provider)
        (provider
         .gcp_storage
         .objects()
         .compose(destinationBucket=cast(GCPBucket, bucket).name,
                  destinationObject=destination,
                  body={'sourceObjects': [{'name': s} for s in sources]})
         .execute())

    def _list_temp_objects(self, bucket: Bucket | str,
                           upload: MultipartUpload) -> builtins.list[str]:
        prefix = self._temp_prefix(upload)
        names: builtins.list[str] = []
        page_token = None
        provider = cast("GCPCloudProvider", self.provider)
        while True:
            response = (
                provider
                .gcp_storage
                .objects()
                .list(bucket=cast(GCPBucket, bucket).name,
                      prefix=prefix, pageToken=page_token)
                .execute())
            names.extend(o['name'] for o in response.get('items', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                return names

    def _delete_objects(self, bucket: Bucket | str, names: builtins.list[str],
                        ignore_missing: bool = False) -> None:
        provider = cast("GCPCloudProvider", self.provider)
        for name in names:
            try:
                (provider
                 .gcp_storage
                 .objects()
                 .delete(bucket=cast(GCPBucket, bucket).name, object=name)
                 .execute())
            except googleapiclient.errors.HttpError:
                if not ignore_missing:
                    raise


class GCPGatewayService(BaseGatewayService):
    _DEFAULT_GATEWAY_NAME = 'default-internet-gateway'
    _GATEWAY_URL_PREFIX = 'global/gateways/'

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPGatewayService, self).__init__(provider)
        self._default_internet_gateway = GCPInternetGateway(
            cast("GCPCloudProvider", provider),
            {'id': (GCPGatewayService._GATEWAY_URL_PREFIX +
                    GCPGatewayService._DEFAULT_GATEWAY_NAME),
             'name': GCPGatewayService._DEFAULT_GATEWAY_NAME})

    @dispatch(event="provider.networking.gateways.get_or_create",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def get_or_create(self, network: Network | str) -> GCPInternetGateway:
        return self._default_internet_gateway

    @dispatch(event="provider.networking.gateways.delete",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def delete(self, network: Network | str, gateway: Gateway) -> None:
        pass

    @dispatch(event="provider.networking.gateways.list",
              priority=BaseGatewayService.STANDARD_EVENT_PRIORITY)
    def list(self, network: Network | str, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPInternetGateway]:
        gws = [self._default_internet_gateway]
        return ClientPagedResultList(self._provider,
                                     gws,
                                     limit=limit, marker=marker)


class GCPFloatingIPService(BaseFloatingIPService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPFloatingIPService, self).__init__(provider)

    @dispatch(event="provider.networking.floating_ips.get",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def get(self, gateway: Gateway,
            floating_ip_id: str) -> GCPFloatingIP | None:
        provider = cast("GCPCloudProvider", self.provider)
        fip = provider.get_resource(
            'addresses', floating_ip_id)
        return (GCPFloatingIP(provider, fip)
                if fip else None)

    @dispatch(event="provider.networking.floating_ips.list",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def list(self, gateway: Gateway, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPFloatingIP]:
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_compute
            .addresses()
            .list(project=provider.project_name,
                  region=self.provider.region_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        ips = [GCPFloatingIP(provider, ip)
               for ip in response.get('items', [])]
        if len(ips) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(ips))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=ips)

    @dispatch(event="provider.networking.floating_ips.create",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def create(self, gateway: Gateway) -> GCPFloatingIP:
        provider = cast("GCPCloudProvider", self.provider)
        region_name = self.provider.region_name
        ip_name = 'ip-{0}'.format(uuid.uuid4())
        response = (
            provider
            .gcp_compute
            .addresses()
            .insert(project=provider.project_name,
                    region=region_name,
                    body={'name': ip_name})
            .execute())
        provider.wait_for_operation(response, region=region_name)
        return self.get(gateway, ip_name)

    @dispatch(event="provider.networking.floating_ips.delete",
              priority=BaseFloatingIPService.STANDARD_EVENT_PRIORITY)
    def delete(self, gateway: Gateway, fip: FloatingIP | str) -> None:
        fip = cast(GCPFloatingIP,
                   fip if isinstance(fip, GCPFloatingIP)
                   else self.get(gateway, fip))
        provider = cast("GCPCloudProvider", self.provider)
        project_name = provider.project_name
        # First, delete the forwarding rule, if there is any.
        # pylint:disable=protected-access
        if fip._rule:
            response = (
                provider
                .gcp_compute
                .forwardingRules()
                .delete(project=project_name,
                        region=fip.region_name,
                        forwardingRule=fip._rule['name'])
                .execute())
            provider.wait_for_operation(response, region=fip.region_name)

        # Release the address.
        response = (
            provider
            .gcp_compute
            .addresses()
            .delete(project=project_name,
                    region=fip.region_name,
                    address=fip._ip['name'])
            .execute())
        provider.wait_for_operation(response, region=fip.region_name)


class GCPDnsService(BaseDnsService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPDnsService, self).__init__(provider)

        # Initialize provider services
        self._zone_svc = GCPDnsZoneService(self.provider)
        self._record_svc = GCPDnsRecordService(self.provider)

    @property
    def host_zones(self) -> GCPDnsZoneService:
        return self._zone_svc

    @property
    def _records(self) -> GCPDnsRecordService:
        return self._record_svc


class GCPDnsZoneService(BaseDnsZoneService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPDnsZoneService, self).__init__(provider)

    @dispatch(event="provider.dns.host_zones.get",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def get(self, dns_zone_id: str) -> GCPDnsZone | None:
        provider = cast("GCPCloudProvider", self.provider)
        dns_zone = provider.get_resource(
            'managedZones', dns_zone_id, project=provider.project_name)
        return GCPDnsZone(provider, dns_zone) if dns_zone else None

    @dispatch(event="provider.dns.host_zones.list",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def list(self, limit: int | None = None,
             marker: str | None = None) -> ResultList[GCPDnsZone]:
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_dns
            .managedZones()
            .list(project=provider.project_name,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        dns_zones = []
        for dns_zone in response.get('managedZones', []):
            dns_zones.append(GCPDnsZone(provider, dns_zone))
        if len(dns_zones) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(dns_zones))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=dns_zones)

    @dispatch(event="provider.dns.host_zones.find",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def find(self, **kwargs: Any) -> ResultList[GCPDnsZone]:
        filters = ['name']
        matches = cb_helpers.generic_find(
            filters, kwargs, list(self))
        return ClientPagedResultList(
            self.provider, cast("builtins.list[GCPDnsZone]", matches),
            limit=None, marker=None)

    @dispatch(event="provider.dns.host_zones.create",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def create(self, name: str, admin_email: str) -> GCPDnsZone:
        GCPDnsZone.assert_valid_resource_name(name)
        body = {
            'kind': 'dns#managedZone',
            'name': cb_helpers.to_resource_name(name),
            'dnsName':  self._get_fully_qualified_dns(name),
            'description': 'admin_email=' + admin_email,
            'visibility': 'public'
        }
        provider = cast("GCPCloudProvider", self.provider)
        try:
            response = (
                provider
                .gcp_dns
                .managedZones()
                .create(project=provider.project_name,
                        body=body)
                .execute())
            return GCPDnsZone(provider, response)
        except googleapiclient.errors.HttpError as http_error:
            # 409 = conflict
            if http_error.resp.status in [409]:
                raise DuplicateResourceException(
                    'DNS Zone already exists with name {0}'.format(name))
            else:
                raise

    @dispatch(event="provider.dns.host_zones.delete",
              priority=BaseDnsZoneService.STANDARD_EVENT_PRIORITY)
    def delete(self, dns_zone: DnsZone | str) -> None:
        zone = (dns_zone if isinstance(dns_zone, GCPDnsZone)
                else self.get(dns_zone))
        if zone:
            provider = cast("GCPCloudProvider", self.provider)
            (provider
             .gcp_dns
             .managedZones()
             .delete(project=provider.project_name,
                     managedZone=zone.id)
             .execute())


class GCPDnsRecordService(BaseDnsRecordService):

    def __init__(self, provider: CloudProvider) -> None:
        super(GCPDnsRecordService, self).__init__(provider)

    def _to_resource_records(self, data: str | builtins.list[str],
                             rec_type: str) -> builtins.list[str]:
        """
        Converts a record to what GCP expects. For example, GCP
        expects a fully qualified name for all CNAME records.
        """
        if isinstance(data, list):
            records = data
        else:
            records = [data]
        return [self._standardize_record(r, rec_type) for r in records]

    def get(self, dns_zone: DnsZone | str,
            rec_id: str) -> GCPDnsRecord | None:
        if rec_id and ":" in rec_id:
            rec_name, rec_type = rec_id.split(":")
            provider = cast("GCPCloudProvider", self.provider)
            response = (
                provider
                .gcp_dns
                .resourceRecordSets()
                .list(project=provider.project_name,
                      managedZone=cast(GCPDnsZone, dns_zone).id,
                      name=self._get_fully_qualified_dns(rec_name),
                      type=rec_type)
                .execute())
            if len(response.get('rrsets', [])) > 1:
                log.warning('Expected at most %d results; got %d',
                            1, len(response.get('items', [])))
            for rec in response.get('rrsets', []):
                return GCPDnsRecord(provider, cast(GCPDnsZone, dns_zone), rec)
            return None
        else:
            return None

    # The interface declares list(dns_zone, limit, marker); this impl also
    # accepts a trailing rec_id filter.
    def list(self, dns_zone: DnsZone | str,  # type: ignore[override]
             limit: int | None = None,
             marker: str | None = None,
             rec_id: str | None = None) -> ResultList[GCPDnsRecord]:
        provider = cast("GCPCloudProvider", self.provider)
        max_result = limit if limit is not None and limit < 500 else 500
        response = (
            provider
            .gcp_dns
            .resourceRecordSets()
            .list(project=provider.project_name,
                  managedZone=cast(GCPDnsZone, dns_zone).id,
                  maxResults=max_result,
                  pageToken=marker)
            .execute())
        records = []
        for rec in response.get('rrsets', []):
            records.append(
                GCPDnsRecord(provider, cast(GCPDnsZone, dns_zone), rec))
        if len(records) > max_result:
            log.warning('Expected at most %d results; got %d',
                        max_result, len(records))
        return ServerPagedResultList('nextPageToken' in response,
                                     response.get('nextPageToken'),
                                     False, data=records)

    def find(self, dns_zone: DnsZone | str,
             **kwargs: Any) -> ResultList[GCPDnsRecord]:
        filters = ['name']
        matches = cb_helpers.generic_find(
            filters, kwargs, list(cast(GCPDnsZone, dns_zone).records))
        return ClientPagedResultList(
            self.provider, cast("builtins.list[GCPDnsRecord]", matches),
            limit=None, marker=None)

    def create(self,
               dns_zone: DnsZone | str, name: str, type: str,
               data: str, ttl: int | None = None) -> GCPDnsRecord:
        GCPDnsRecord.assert_valid_resource_name(name)
        body = {
            'kind': 'dns#change',
            "additions": [
                {
                    'kind': 'dns#resourceRecordSet',
                    'name': self._get_fully_qualified_dns(name),
                    'type': type,
                    'ttl': ttl,
                    'rrdatas': self._to_resource_records(data, type)
                }
            ]
        }
        provider = cast("GCPCloudProvider", self.provider)
        (provider
         .gcp_dns
         .changes()
         .create(project=provider.project_name,
                 managedZone=cast(GCPDnsZone, dns_zone).id,
                 body=body)
         .execute())
        rec_id = name + ":" + type
        record = self.get(dns_zone, rec_id)
        if record is None:
            raise ProviderInternalException(
                "DNS record not found after creation")
        return record

    def delete(self, dns_zone: DnsZone | str,
               record: GCPDnsRecord | str) -> None:
        # NOTE: previously called self.get(record) with a single argument,
        # which is invalid (get requires the dns_zone too). Pass dns_zone so
        # a record id can be resolved.
        rec = (record if isinstance(record, GCPDnsRecord)
               else self.get(dns_zone, record))

        if rec:
            body = {
                'kind': 'dns#change',
                "deletions": [
                    {
                        'kind': 'dns#resourceRecordSet',
                        'name': self._get_fully_qualified_dns(rec.name),
                        'type': rec.type,
                        'ttl': rec.ttl,
                        'rrdatas': self._to_resource_records(
                            rec.data, rec.type)
                    }
                ]
            }
            provider = cast("GCPCloudProvider", self.provider)
            (provider
             .gcp_dns
             .changes()
             .create(project=provider.project_name,
                     managedZone=cast(GCPDnsZone, dns_zone).id,
                     body=body)
             .execute())
